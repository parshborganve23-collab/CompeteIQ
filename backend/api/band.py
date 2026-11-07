"""API routes for BAND AI multi-agent integration.

Reports real connection status. All agent communication goes through the actual
BAND AI API when configured; otherwise returns disconnected state with setup
instructions. Never fakes successful agent communication.
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from integrations import band_integration, hindsight_integration

router = APIRouter(tags=["BAND AI Agents"])


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage(
    stages: List[dict], stage: str, status: str, detail: str = "", error: str = ""
):
    entry = {
        "stage": stage,
        "status": status,  # ok | skipped | failed
        "detail": detail,
        "error": error,
        "at": _iso_now_utc(),
    }
    stages.append(entry)
    return entry


def _stored_room_for_event(db: Session, event_id: str) -> str:
    """Return the stored BAND room reference for this event, if any.

    One shared room is kept per intelligence event, so repeated workflow runs
    never create duplicate rooms for individual messages.
    """
    row = (
        db.query(models.StrategicRecommendation)
        .filter(
            models.StrategicRecommendation.event_id == event_id,
            models.StrategicRecommendation.band_room_id != "",
        )
        .order_by(models.StrategicRecommendation.created_at.desc())
        .first()
    )
    if row:
        return row.band_room_id
    run = (
        db.query(models.WorkflowRun)
        .filter(
            models.WorkflowRun.event_id == event_id,
            models.WorkflowRun.band_room_id != "",
        )
        .order_by(models.WorkflowRun.created_at.desc())
        .first()
    )
    return (run.band_room_id if run else "") or ""


@router.get("/room/{room_id}/messages")
def band_room_messages(room_id: str):
    """Return the real BAND room transcript (aggregated across all 7 agents).

    The Agent API returns each agent's own delivery view, so this merges the
    per-agent message lists and deduplicates by message ID. All content comes
    from the real Band API.
    """
    try:
        band_integration.initialize()
    except Exception:  # noqa: BLE001
        pass
    if not band_integration.is_available():
        raise HTTPException(status_code=503, detail="BAND AI is not available.")
    try:
        messages = band_integration.list_room_messages(room_id)
        participants = band_integration.room_participants(room_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"room_id": room_id, "participants": participants, "messages": messages}



@router.get("/status")
def band_status(refresh: bool = False):
    """Return live BAND AI status for all seven per-agent credentials."""
    if refresh:
        band_integration.initialize(force=True)
    status = band_integration.status()
    return {
        "configured": status.configured,
        "available": status.available,
        "reason": status.reason,
        "setup_instructions": status.setup_instructions,
        "agents": status.agents,
        "authenticated_count": status.authenticated_count,
        "configured_count": status.configured_count,
        "rest_base": status.rest_base,
    }


@router.get("/agents")
def band_agents():
    """List the seven specialized BAND AI agents with live auth state."""
    return {"agents": band_integration.list_agents()}


@router.post("/message")
def band_send_message(
    payload: Optional[schemas.BandMessageIn] = Body(None),
    agent_name: Optional[str] = None,
    message: Optional[str] = None,
    task: str = "",
    handoff_to: Optional[str] = None,
    recommendation_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Send a real Band chat message to a registered agent.

    Accepts the JSON body used by the frontend as well as the original query
    parameters. Optionally stores the message against a recommendation.
    """
    agent_name = payload.agent_name if payload else agent_name
    message = payload.message if payload else message
    task = payload.task if payload else task
    handoff_to = payload.handoff_to if payload else handoff_to
    recommendation_id = (
        payload.recommendation_id if payload else recommendation_id
    )

    if not agent_name or not message:
        raise HTTPException(
            status_code=422,
            detail="Both agent_name and message are required.",
        )

    if not band_integration.is_available():
        status = band_integration.status()
        raise HTTPException(
            status_code=503,
            detail={
                "error": "BAND AI not available",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
            },
        )
    try:
        result = band_integration.send_message(
            agent_name=agent_name,
            message=message,
            task=task,
            handoff_to=handoff_to,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Persist agent message to the database if a recommendation exists
    if recommendation_id:
        rec = db.query(models.StrategicRecommendation).filter_by(id=recommendation_id).first()
        if rec:
            msg = models.AgentMessage(
                recommendation_id=recommendation_id,
                agent_name=result["agent_name"],
                agent_role=result.get("agent_role", ""),
                task=result.get("task", task),
                status=result.get("status", "completed"),
                message=result.get("message", message),
                output=result.get("output", ""),
                handoff_to=result.get("handoff_to", handoff_to or ""),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            result["stored_message_id"] = msg.id

    return result


@router.post("/workflow/{event_id}")
async def band_workflow(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Run the unified CompeteIQ + BAND + Hindsight workflow for an event.

    1.  Store / validate the event and evidence (CompeteIQ DB = source of truth).
    2.  Recall relevant historical memories from the Hindsight bank (real API),
        then run reflect (real API) for the historical synthesis.
    3.  Find or create one shared BAND room for the event (reuse stored room
        reference; no duplicate rooms) and publish the event into the room.
    4.  Dispatch each of the seven agents with a real BAND message; the
        Historical Intelligence Agent receives the real recalled memories and
        the Strategy Agent receives the real reflect synthesis.
    5.  Persist every real BAND message ID, sender and timestamp.
    6.  Save a strategic recommendation record linked by the same workflow ID.

    Agent findings (their actual Band replies) are collected asynchronously by
    the persistent band_worker.py process and stored when the workflow is
    finalized via /api/workflows/{workflow_id}/finalize — which also retains
    the completed experience in Hindsight and posts the final recommendation
    summary to the room. Nothing is fabricated here: stages that fail keep the
    real error text and the run status reflects it.
    """
    event = db.query(models.IntelligenceEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Intelligence event not found")

    if not band_integration.is_available():
        status = band_integration.status()
        raise HTTPException(
            status_code=503,
            detail={
                "error": "BAND AI not available",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
            },
        )

    event_dict = {
        "id": event.id,
        "title": event.title,
        "company": event.company,
        "category": event.category,
        "description": event.description,
    }
    stages: List[dict] = []
    _stage(stages, "event_validated", "ok", detail=f"Event '{event.title}' found in CompeteIQ database.")

    # Create the unified workflow record first so every participant shares the
    # same workflow ID across CompeteIQ, BAND and Hindsight.
    workflow = models.WorkflowRun(event_id=event.id, status="running", stages=stages)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    hindsight_available = hindsight_integration.is_available()

    # ---- Hindsight: recall relevant historical memories (real API) ----
    historical_context = ""
    recall_refs: List[dict] = []
    if hindsight_available:
        recall_error = ""
        for attempt in range(2):  # one retry — transient Hindsight network failures recover after its lazy 20s cooldown
            try:
                memories = await hindsight_integration.arecall(
                    query=f"{event.title} {event.description} {event.company} {event.category}",
                    bank_id=hindsight_integration.BANK_COMPETEIQ,
                    limit=10,
                )
                recall_error = ""
                break
            except RuntimeError as exc:
                recall_error = str(exc)
                if attempt == 0:
                    await asyncio.sleep(15)  # let the lazy-init cooldown recover, then retry once
        if recall_error:
            workflow.error = recall_error
            _stage(stages, "hindsight_recall", "failed", error=recall_error)
            hindsight_available = False
        else:
            recall_refs = [
                {"id": m["id"], "content": m["content"][:280], "score": m.get("score")}
                for m in memories
            ]
            workflow.hindsight_recall_refs = recall_refs
            workflow.hindsight_recall_count = len(recall_refs)
            context_parts = [f"- [memory {m['id']}] {m['content'][:300]}" for m in memories]
            historical_context = "\n".join(context_parts)
            _stage(
                stages,
                "hindsight_recall",
                "ok",
                detail=f"Recalled {len(recall_refs)} memories from bank '{hindsight_integration.BANK_COMPETEIQ}'.",
            )
    else:
        _stage(stages, "hindsight_recall", "skipped", error="Hindsight is not available.")

    # ---- Hindsight: reflect to synthesize historical insights (real API) ----
    reflection_text = ""
    if hindsight_available:
        reflect_error = ""
        reflection = None
        for attempt in range(2):  # one retry after the lazy-init cooldown
            try:
                reflection_context_parts = (
                    f"Current competitor event: {event.title} ({event.company}, {event.category})\n"
                    f"Description: {event.description}\n\n"
                    f"Recalled historical memories:\n{historical_context}\n\n"
                    "Synthesize these historical experiences into higher-level strategic "
                    "insights for NEXORA AI: what pattern repeats, what previously worked, "
                    "what previously failed, and what that means for this event."
                )
                reflection = await hindsight_integration.areflect(
                    query=reflection_context_parts,
                    bank_id=hindsight_integration.BANK_COMPETEIQ,
                    context="competeiq-history-synthesis",
                )
                reflect_error = ""
                break
            except RuntimeError as exc:
                reflect_error = str(exc)
                if attempt == 0:
                    await asyncio.sleep(15)
        if reflect_error or reflection is None:
            workflow.error = reflect_error
            _stage(stages, "hindsight_reflect", "failed", error=reflect_error)
        else:
            reflection_text = reflection.get("reflection", "")
            workflow.hindsight_reflection_text = reflection_text
            _stage(stages, "hindsight_reflect", "ok", detail="Reflect synthesis retrieved from Hindsight.")
    else:
        _stage(stages, "hindsight_reflect", "skipped", error="Hindsight is not available.")

    db.commit()
    db.refresh(workflow)

    # ---- BAND: find or create the shared room (stored reference; no duplicates) ----
    stored_room_id = _stored_room_for_event(db, event.id)
    try:
        room_id = await asyncio.to_thread(
            band_integration._ensure_room,
            room_id=stored_room_id,
            title=f"CompeteIQ: {event.title}"[:100],
        )
    except RuntimeError as exc:
        workflow.status = "failed"
        workflow.stages = stages
        workflow.error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc))

    workflow.band_room_id = room_id
    workflow.band_room_title = f"CompeteIQ: {event.title}"[:100]
    _stage(
        stages,
        "band_room",
        "ok",
        detail=f"Shared BAND room {'reused' if stored_room_id and stored_room_id == room_id else 'created'}: {room_id}",
    )

    # ---- BAND: STEP 3 — publish the original event into the room ----
    event_publication_text = (
        f"[CompeteIQ Workflow {workflow.id}]\n"
        f"Competitor event: {event.title}\n"
        f"Company: {event.company} | Category: {event.category}\n"
        f"Description: {event.description}\n"
        f"Evidence source: {event.source_url or 'n/a'}\n"
        f"Published: {event.publication_date or _iso_now_utc()}"
    )
    try:
        event_pub = await asyncio.to_thread(
            band_integration.publish_room_message,
            room_id,
            event_publication_text,
        )
        workflow.event_published_message_id = event_pub.get("message_id", "") or ""
        _stage(
            stages,
            "band_event_published",
            "ok",
            detail=f"Event published into the room as message {workflow.event_published_message_id}.",
        )
    except RuntimeError as exc:
        _stage(stages, "band_event_published", "failed", error=str(exc))
        workflow.error = str(exc)
        # Preserve the run; dispatches below can still succeed.

    db.commit()
    db.refresh(workflow)
    published_message_id = workflow.event_published_message_id

    try:
        results = await asyncio.to_thread(
            band_integration.run_workflow,
            event_dict,
            historical_context=historical_context,
            reflection_text=reflection_text,
            stored_room_id=room_id,
        )
    except RuntimeError as exc:
        workflow.status = "failed"
        workflow.stages = stages
        workflow.error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc))

    # ---- Create the recommendation record linked to the workflow ----
    recommendation = models.StrategicRecommendation(
        event_id=event.id,
        workflow_type="band-ai",
        event_summary=event.title,
        impact_on_nexora=event.impact_on_nexora or "",
        evidence_sources=event.source_url or "",
        confidence_score="medium",
        status="pending",
        workflow_id=workflow.id,
        band_room_id=room_id,
        hindsight_memory_refs=recall_refs,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    workflow.recommendation_id = recommendation.id
    db.commit()
    db.refresh(workflow)

    # Persist the room publication as an event_publish row (real band id).
    if published_message_id:
        db.add(
            models.AgentMessage(
                recommendation_id=recommendation.id,
                agent_name="Strategy Agent",  # published by the room owner
                agent_role="CompeteIQ backend (room owner)",
                task="Publish the original competitor intelligence event into the BAND room.",
                status="sent",
                message=event_publication_text,
                output="",
                handoff_to="",
                workflow_id=workflow.id,
                band_message_id=published_message_id,
                band_sent_at=_iso_now_utc(),
                sender_name="Strategy Agent",
                direction="event_publish",
            )
        )
        db.commit()

    # ---- Persist each real BAND dispatch as a message row ----
    stored_messages: List[dict] = []
    for r in results:
        raw_sent_at = r.get("dispatched_at")
        sent_at = raw_sent_at.isoformat() if hasattr(raw_sent_at, "isoformat") else (raw_sent_at or "")
        msg = models.AgentMessage(
            recommendation_id=recommendation.id,
            agent_name=r.get("agent_name", ""),
            agent_role=r.get("agent_role", ""),
            task=r.get("task", ""),
            status=r.get("status", "pending"),
            message=r.get("message", ""),
            output=r.get("output", ""),
            handoff_to=r.get("handoff_to", ""),
            workflow_id=workflow.id,
            band_message_id=r.get("message_id", "") or "",
            band_sent_at=sent_at,
            sender_name=r.get("sender", "") or "",
            direction="dispatch",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        stored_messages.append(schemas.AgentMessageOut.model_validate(msg))

    # ---- Workflow status: dispatches that were actually sent ----
    sent_statuses = [r.get("status") for r in results]
    if all(s == "sent" for s in sent_statuses):
        workflow.status = "dispatched"
        _stage(stages, "band_dispatch", "ok", detail="All 7 agent task dispatches were sent as real BAND messages.")
    elif any(s == "failed" for s in sent_statuses):
        failed_steps = [r.get("agent_name") for r in results if r.get("status") == "failed"]
        workflow.error = f"Dispatch failed for: {', '.join(failed_steps)}"
        workflow.status = "partial"
        _stage(
            stages,
            "band_dispatch",
            "partial",
            detail=f"{len(failed_steps)} dispatches failed: {', '.join(failed_steps)}; failed dispatch errors are stored with the workflow error. Successful messages are preserved.",
        )
    else:
        workflow.status = "partial"
        _stage(stages, "band_dispatch", "partial", detail="Some dispatches were not sent.")

    workflow.stages = stages
    db.commit()
    db.refresh(workflow)

    return {
        "workflow_id": workflow.id,
        "recommendation_id": recommendation.id,
        "workflow": "unified-band-hindsight",
        "agents": stored_messages,
        "agent_count": len(stored_messages),
        "final_output": "".join(m.output for m in stored_messages if m.output),
        "chat_id": room_id,
        "band_room": {
            "room_id": room_id,
            "room_title": workflow.band_room_title,
            "room_url": None,  # Band's Agent API does not expose web room URLs
            "participants": await asyncio.to_thread(
                band_integration.room_participants, room_id
            ),
        },
        "hindsight": {
            "bank_id": (
                hindsight_integration.BANK_COMPETEIQ
                if hindsight_available
                else hindsight_integration.BANK_COMPETEIQ
            ),
            "available": hindsight_available,
            "recall_count": len(recall_refs),
            "recall_refs": recall_refs,
            "reflection": reflection_text,
            "retained": False,  # experience is retained at finalize, after real agent findings exist
        },
        "stages": stages,
        "status": workflow.status,
        "band_available": True,
    }
