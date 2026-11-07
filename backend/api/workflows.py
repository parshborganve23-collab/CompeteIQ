"""Unified workflow history API.

Connects a CompeteIQ IntelligenceEvent, its BAND collaboration room and
messages, its Hindsight memory references and its final strategic
recommendation under the same workflow ID. Agent findings are the real Band
room replies (sender identity must match a registered agent); dispatched
tool-result events are never treated as agent analysis responses.

Hindsight retention happens at finalize with idempotency (stable workflow ID,
never retained twice). Nothing is fabricated: failed stages keep the real
error text while previously successful operations are preserved.
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from integrations import band_integration, hindsight_integration

router = APIRouter(tags=["Unified Workflows"])


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage(stages: List[dict], stage: str, status: str, detail: str = "", error: str = ""):
    stages.append(
        {
            "stage": stage,
            "status": status,  # ok | skipped | failed
            "detail": detail,
            "error": error,
            "at": _iso_now_utc(),
        }
    )
    return stages[-1]


def _authenticated_agent_by_id() -> Dict[str, dict]:
    return {
        state["remote_id"]: state
        for state in band_integration._agent_states.values()
        if state.get("authenticated") and state.get("remote_id")
    }


def _room_room_title(workflow: models.WorkflowRun) -> str:
    return workflow.band_room_title or ""


def _live_room(band_room_id: str) -> dict:
    """Fetch real room participants + transcript (empty on failure)."""
    band_integration.initialize()
    room: dict = {
        "room_id": band_room_id,
        "room_title": "",
        "room_url": "",  # Band's Agent API does not expose web room URLs
        "participants": [],
        "messages": [],
    }
    if not band_integration.is_available():
        return room
    try:
        room["messages"] = band_integration.list_room_messages(band_room_id)
    except RuntimeError:
        room["messages"] = []
    try:
        room["participants"] = band_integration.room_participants(band_room_id)
    except RuntimeError:
        room["participants"] = []
    return room


def _clean_band_content(content: str) -> str:
    """Strip Band platform artifacts: mention tokens and '[Sender]: ' prefixes.

    Mentions are stored as ``@[[agent-uuid]]`` inside the message content;
    they are platform routing artifacts, not part of the agent's analysis.
    """
    text = re.sub(r"@\[\[[^\]]*\]\]", "", content or "")
    if text.startswith("["):
        prefix_split = text.split("]: ", 1)
        if len(prefix_split) == 2 and len(prefix_split[0]) < 120:
            text = prefix_split[1]
    return text.strip()


def _backend_published_ids(db: Session, workflow: models.WorkflowRun) -> set:
    """IDs of messages our backend itself posted into the room.

    The event publication and any final-summary posts are made by the room
    owner (Strategy Agent's identity), so they must never be mistaken for
    real agent analysis responses.
    """
    ids = {workflow.event_published_message_id or "", workflow.strategy_final_message_id or ""}
    for m in (
        db.query(models.AgentMessage)
        .filter(
            models.AgentMessage.workflow_id == workflow.id,
            models.AgentMessage.direction.in_(["event_publish", "dispatch"]),
        )
        .all()
    ):
        if m.band_message_id:
            ids.add(m.band_message_id)
    return {i for i in ids if i}


def _sync_agent_replies(db: Session, workflow: models.WorkflowRun) -> tuple[List[dict], List[models.AgentMessage], Optional[dict]]:
    """Persist new real agent replies from the live BAND room transcript.

    A genuine agent reply is a text message whose sender_id matches a
    registered agent's real Band identity. Returns (new replies, all rows,
    the Strategy Agent's most recent real reply if present).
    """
    room = _live_room(workflow.band_room_id)
    agent_map = _authenticated_agent_by_id()

    messages = (
        db.query(models.AgentMessage)
        .filter_by(workflow_id=workflow.id)
        .order_by(models.AgentMessage.timestamp.asc())
        .all()
    )
    known_ids = {m.band_message_id for m in messages if m.band_message_id}

    strategy_reply: Optional[dict] = None
    dry_runs: List[dict] = []
    published_ids = _backend_published_ids(db, workflow)
    for m in room.get("messages", []):
        state = agent_map.get(m.get("sender_id", ""))
        if not state or m.get("message_type") != "text":
            continue
        m_id = m.get("id", "")
        if m_id in published_ids or m_id in known_ids:
            continue
        clean_content = _clean_band_content(m.get("content", ""))
        if clean_content.startswith("[CompeteIQ Workflow"):
            # Our own event publication / completion summary post — never an
            # agent analysis response even if the row was missed.
            continue
        if state["key"] == "strategy" and (
            strategy_reply is None or (m.get("created_at") or "") >= (strategy_reply.get("created_at") or "")
        ):
            strategy_reply = m
        known_ids.add(m_id)
        record = models.AgentMessage(
            recommendation_id=workflow.recommendation_id or "",
            agent_name=state["name"],
            agent_role=state["role"],
            task="Agent reply collected from the real BAND room.",
            status="completed",
            message=clean_content[:4000],
            output=clean_content,
            handoff_to="",
            workflow_id=workflow.id,
            band_message_id=m_id,
            band_sent_at=m.get("created_at", ""),
            sender_name=state["name"],
            direction="agent_reply",
        )
        db.add(record)
        db.flush()
        messages.append(record)
        dry_runs.append(
            {
                "agent_name": state["name"],
                "band_message_id": m_id,
                "content": clean_content,
                "created_at": m.get("created_at", ""),
                "stored_agent_message_id": record.id,
            }
        )
    db.commit()
    db.refresh(workflow)
    return dry_runs, messages, strategy_reply


@router.get("")
def list_workflows(db: Session = Depends(get_db)):
    """List recent unified workflow runs with their cross-platform references."""
    runs = (
        db.query(models.WorkflowRun)
        .order_by(models.WorkflowRun.created_at.desc())
        .limit(50)
        .all()
    )
    events = {e.id: e for e in db.query(models.IntelligenceEvent).all()}
    out = []
    for run in runs:
        event = events.get(run.event_id)
        out.append(
            {
                "workflow_id": run.id,
                "event_id": run.event_id,
                "event_title": event.title if event else "",
                "event_company": event.company if event else "",
                "event_category": event.category if event else "",
                "recommendation_id": run.recommendation_id,
                "status": run.status,
                "band_room_id": run.band_room_id,
                "band_room_title": run.band_room_title,
                "hindsight_recall_count": run.hindsight_recall_count,
                "hindsight_retained_at": run.hindsight_retained_at,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "error": (run.error or "")[:200],
            }
        )
    return {"workflows": out, "count": len(out)}


@router.get("/{workflow_id}")
def workflow_detail(workflow_id: str, sync: bool = True, db: Session = Depends(get_db)):
    """Full unified detail: event, room, real messages, Hindsight refs, recommendation.

    ``?sync=true`` (default) also pulls the live BAND room transcript and
    stores any not-yet-persisted real agent replies deduped by Band message ID.
    """
    workflow = db.query(models.WorkflowRun).filter_by(id=workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    event = db.query(models.IntelligenceEvent).filter_by(id=workflow.event_id).first()
    recommendation = (
        db.query(models.StrategicRecommendation)
        .filter_by(id=workflow.recommendation_id)
        .first()
        if workflow.recommendation_id
        else None
    )

    new_replies: List[dict] = []
    messages: List[models.AgentMessage] = []
    if workflow.band_room_id and sync:
        new_replies, messages, _ = _sync_agent_replies(db, workflow)
    else:
        messages = (
            db.query(models.AgentMessage)
            .filter_by(workflow_id=workflow.id)
            .order_by(models.AgentMessage.timestamp.asc())
            .all()
        )

    room = _live_room(workflow.band_room_id) if workflow.band_room_id else None
    if room is not None:
        room["room_title"] = _room_room_title(workflow)

    hindsight_ok = hindsight_integration.is_available()
    recalled = workflow.hindsight_recall_refs or []
    retained_refs = workflow.hindsight_retained_refs or []

    return {
        "workflow_id": workflow.id,
        "status": workflow.status,
        "stages": workflow.stages or [],
        "error": workflow.error or "",
        "started_at": workflow.started_at,
        "completed_at": workflow.completed_at,
        "event": schemas.IntelligenceEventOut.model_validate(event).model_dump()
        if event
        else None,
        "band_room": room,
        "agent_messages": [
            schemas.AgentMessageOut.model_validate(m).model_dump() for m in messages
        ],
        "agent_replies_new": new_replies,
        "hindsight": {
            "bank_id": hindsight_integration.BANK_COMPETEIQ,
            "available": hindsight_ok,
            "recall_count": workflow.hindsight_recall_count,
            "recall_refs": recalled,
            "reflection": workflow.hindsight_reflection_text or "",
            "retained_refs": retained_refs,
            "retained_at": workflow.hindsight_retained_at or "",
        },
        "recommendation": schemas.StrategicRecommendationOut.model_validate(
            recommendation
        ).model_dump()
        if recommendation
        else None,
    }


@router.post("/{workflow_id}/finalize")
async def finalize_workflow(
    workflow_id: str,
    payload: Optional[schemas.WorkflowFinalizeIn] = Body(None),
    db: Session = Depends(get_db),
):
    """Finalize a unified workflow run using REAL data only.

    1. Collect actual agent replies from the real BAND room transcript
       (registered agent sender identity requirement; no tool-result events)
       and persist them deduped by Band message ID.
    2. Use the Strategy Agent's real reply as the consolidated final
       recommendation (only when it really exists in the room).
    3. Retain the completed experience in Hindsight with the stable workflow
       ID (idempotent: skipped if this workflow was already retained).
    4. Record failed stages with their real error while keeping everything
       that succeeded before the failure intact.
    """
    workflow = db.query(models.WorkflowRun).filter_by(id=workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if not workflow.band_room_id:
        raise HTTPException(status_code=409, detail="Workflow has no BAND room reference.")

    feedback = payload.user_feedback if payload else ""
    outcome = payload.outcome if payload else ""

    stages = workflow.stages or []

    _, messages, strategy_reply = await asyncio.to_thread(
        _sync_agent_replies, db, workflow
    )
    band_worked = band_integration.is_available()
    room = await asyncio.to_thread(_live_room, workflow.band_room_id)

    if band_worked:
        _stage(
            stages,
            "band_agent_replies",
            "ok",
            detail=(
                f"{len(messages)} total rows; agent replies now synced from room "
                f"{workflow.band_room_id} ({len(room.get('messages', []))} room messages)."
                if room.get("messages")
                else "The BAND room has no messages yet."
            ),
        )

    # ---- Strategy Agent's real reply becomes the final recommendation ----
    final_recommendation_text = ""
    if strategy_reply is not None:
        clean = _clean_band_content(strategy_reply.get("content", ""))
        final_recommendation_text = clean
        recommendation = (
            db.query(models.StrategicRecommendation)
            .filter_by(id=workflow.recommendation_id)
            .first()
            if workflow.recommendation_id
            else None
        )
        if recommendation and clean.strip():
            recommendation.recommended_strategy = clean.strip()
            if feedback:
                recommendation.action_taken = feedback
            if outcome:
                recommendation.outcome_recorded = outcome
            db.commit()
        if not workflow.strategy_final_message_id:
            workflow.strategy_final_message_id = strategy_reply.get("id", "")
        workflow.strategy_final_message_id = completion_message_id
        _stage(
            stages,
            "final_recommendation",
            "ok",
            detail=f"Real Strategy Agent reply (message {strategy_reply.get('id', '')}) stored as the final recommendation.",
        )
    else:
        _stage(
            stages,
            "final_recommendation",
            "skipped",
            error="No real Strategy Agent reply exists in the BAND room yet. Run the band workers, then finalize again after the agents have responded.",
        )

    # ---- STEP 10: publish the final recommendation + completion summary ----
    completion_message_id = workflow.strategy_final_message_id
    if final_recommendation_text and band_worked:
        try:
            summary = await asyncio.to_thread(
                band_integration.publish_room_message,
                workflow.band_room_id,
                (
                    f"[CompeteIQ Workflow {workflow.id}] Workflow completed.\n"
                    f"Final strategic recommendation is stored in CompeteIQ:\n"
                    f"{final_recommendation_text[:1500]}"
                ),
            )
            completion_message_id = summary.get("message_id", "") or completion_message_id
            _stage(
                stages,
                "completion_summary_published",
                "ok",
                detail=f"Completion summary published into the room as message {completion_message_id}.",
            )
        except RuntimeError as exc:
            _stage(
                stages,
                "completion_summary_published",
                "failed",
                error=str(exc),
            )

    # ---- Retain the completed experience in Hindsight (idempotent) ----
    hindsight_ok = hindsight_integration.is_available()
    if not hindsight_ok:
        _stage(stages, "hindsight_retain", "skipped", error="Hindsight is not available.")
    elif workflow.hindsight_retained_at:
        _stage(
            stages,
            "hindsight_retain",
            "skipped",
            detail=f"Experience for workflow {workflow.id} was already retained at {workflow.hindsight_retained_at} (idempotency check passed).",
        )
    else:
        event = (
            db.query(models.IntelligenceEvent)
            .filter_by(id=workflow.event_id)
            .first()
        )
        real_reply_rows = [m for m in messages if m.direction == "agent_reply"]
        reply_blocks = [
            f"- {m.agent_name}: {m.output[:500]}" for m in real_reply_rows
        ]
        if not reply_blocks:
            reply_blocks = [
                f"- {m.agent_name} ({m.status}): dispatched as BAND message {m.band_message_id or 'n/a'}"
                for m in messages
                if m.direction == "dispatch"
            ]

        recommendation = (
            db.query(models.StrategicRecommendation)
            .filter_by(id=workflow.recommendation_id)
            .first()
            if workflow.recommendation_id
            else None
        )
        retain_content = (
            f"CompeteIQ unified workflow experience [{workflow.id}]\n"
            f"Competitor event: {event.title if event else workflow.event_id}\n"
            f"Company: {event.company if event else ''} | Category: {event.category if event else ''}\n"
            f"Description: {event.description if event else ''}\n"
            f"Evidence source: {event.source_url if event else ''}\n"
            f"Agent collaboration (real BAND room messages):\n"
            + ("\n".join(reply_blocks) if reply_blocks else "- No BAND room messages recorded.")
        )
        final_rec = (
            (recommendation.recommended_strategy if recommendation else "")
            or final_recommendation_text
        )
        if final_rec:
            retain_content += f"\nFinal strategic recommendation:\n{final_rec[:2000]}"
        if feedback:
            retain_content += f"\nUser feedback: {feedback}"
        if outcome:
            retain_content += f"\nRecorded outcome: {outcome}"

        try:
            retained = await hindsight_integration.aretain(
                content=retain_content,
                bank_id=hindsight_integration.BANK_COMPETEIQ,
                metadata={
                    "source": "competeiq-unified-workflow",
                    "workflow_id": workflow.id,
                    "event_id": workflow.event_id,
                    "recommendation_id": workflow.recommendation_id,
                    "company": event.company if event else "",
                    "category": event.category if event else "",
                    "type": "unified_workflow_experience",
                },
                context="competeiq-strategy",
            )
            workflow.hindsight_retained_refs = [retained.get("operation_id") or ""]
            workflow.hindsight_retained_at = retained.get("retained_at") or _iso_now_utc()
            if recommendation:
                recommendation.hindsight_retained_at = workflow.hindsight_retained_at
            db.commit()
            _stage(
                stages,
                "hindsight_retain",
                "ok",
                detail=(
                    f"Experience retained in bank '{hindsight_integration.BANK_COMPETEIQ}' "
                    f"(operation {retained.get('operation_id')})."
                ),
            )
        except RuntimeError as exc:
            _stage(stages, "hindsight_retain", "failed", error=str(exc))
            workflow.error = (
                (workflow.error + "; " if workflow.error else "") + str(exc)
            )

    # ---- Completion status (honest) ----
    if band_worked and strategy_reply is not None and workflow.hindsight_retained_at:
        workflow.status = "completed"
        workflow.completed_at = _iso_now_utc()
    elif final_recommendation_text or workflow.hindsight_retained_at:
        workflow.status = "partial"
    elif band_worked:
        workflow.status = "awaiting-agent-replies"

    workflow.stages = stages
    recommendation = (
        db.query(models.StrategicRecommendation)
        .filter_by(id=workflow.recommendation_id)
        .first()
        if workflow.recommendation_id
        else None
    )
    if recommendation:
        recommendation.workflow_id = workflow.id
        recommendation.band_room_id = workflow.band_room_id or recommendation.band_room_id
    db.commit()
    db.refresh(workflow)

    refreshed_messages = (
        db.query(models.AgentMessage)
        .filter_by(workflow_id=workflow.id)
        .order_by(models.AgentMessage.timestamp.asc())
        .all()
    )
    return {
        "workflow_id": workflow.id,
        "status": workflow.status,
        "stages": stages,
        "agent_replies_count": sum(1 for m in refreshed_messages if m.direction == "agent_reply"),
        "dispatch_count": sum(1 for m in refreshed_messages if m.direction == "dispatch"),
        "final_recommendation": (
            recommendation.recommended_strategy if recommendation else final_recommendation_text
        ),
        "strategy_final_message_id": workflow.strategy_final_message_id,
        "hindsight": {
            "bank_id": hindsight_integration.BANK_COMPETEIQ,
            "available": hindsight_ok,
            "retained": bool(workflow.hindsight_retained_at),
            "retained_at": workflow.hindsight_retained_at,
            "retained_refs": workflow.hindsight_retained_refs or [],
        },
        "agent_messages": [
            schemas.AgentMessageOut.model_validate(m).model_dump() for m in refreshed_messages
        ],
        "band_room": {
            "room_id": workflow.band_room_id,
            "room_title": _room_room_title(workflow),
            "room_url": None,
            "participants": room.get("participants", []),
        },
    }
