"""API routes for Hindsight Memory integration.

Reports real connection status. All operations call the actual Hindsight API
when configured; otherwise return disconnected state with setup instructions.
Never simulates successful Hindsight responses.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from integrations import hindsight_integration

router = APIRouter(tags=["Hindsight Memory"])


@router.get("/status", response_model=schemas.HindsightStatusOut)
async def hindsight_status():
    """Return live Hindsight connection status and setup instructions.

    This awaits initialization (startup usually completes it first) so the
    reported state reflects the real Hindsight API connection.
    """
    status = await hindsight_integration.astatus()
    return {
        "configured": status.configured,
        "available": status.available,
        "reason": status.reason,
        "banks": status.banks,
        "setup_instructions": status.setup_instructions,
        "version": status.version,
    }


@router.post("/recall")
async def hindsight_recall(payload: schemas.HindsightRecallIn):
    """Recall memories from a Hindsight bank (real API)."""
    try:
        memories = await hindsight_integration.arecall(
            query=payload.query,
            bank_id=payload.bank_id,
            limit=payload.limit,
            budget=payload.budget,
        )
        return {"bank_id": payload.bank_id, "query": payload.query, "memories": memories, "count": len(memories)}
    except RuntimeError as exc:
        status = hindsight_integration.status()
        raise HTTPException(
            status_code=502 if status.available else 503,
            detail={
                "error": "Hindsight operation failed",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
                "detail": str(exc),
            },
        )


@router.post("/retain")
async def hindsight_retain(payload: schemas.HindsightRetainIn):
    """Retain (store) a memory in a Hindsight bank (real API)."""
    try:
        return await hindsight_integration.aretain(
            content=payload.content,
            bank_id=payload.bank_id,
            metadata=payload.metadata or {},
            context=payload.context,
        )
    except RuntimeError as exc:
        status = hindsight_integration.status()
        raise HTTPException(
            status_code=502 if status.available else 503,
            detail={
                "error": "Hindsight operation failed",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
                "detail": str(exc),
            },
        )


@router.post("/reflect")
async def hindsight_reflect(payload: schemas.HindsightReflectIn):
    """Run agentic reasoning over a Hindsight bank (real API)."""
    try:
        return await hindsight_integration.areflect(
            query=payload.query,
            bank_id=payload.bank_id,
            budget=payload.budget,
            context=payload.context,
        )
    except RuntimeError as exc:
        status = hindsight_integration.status()
        raise HTTPException(
            status_code=502 if status.available else 503,
            detail={
                "error": "Hindsight operation failed",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
                "detail": str(exc),
            },
        )


@router.get("/memories")
async def hindsight_memories(limit: int = 20, search_query: Optional[str] = None):
    """List memories currently in the real Hindsight bank (real API).

    Returns only what the Hindsight API actually returns. If the listing
    fails, the failure is reported honestly instead of inventing counts.
    """
    try:
        items = await hindsight_integration.alist_memories(
            bank_id=hindsight_integration.BANK_COMPETEIQ,
            search_query=search_query,
            limit=max(1, min(limit, 100)),
        )
    except RuntimeError as exc:
        status = hindsight_integration.status()
        raise HTTPException(
            status_code=502 if status.available else 503,
            detail={
                "error": "Hindsight list_memories failed",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
                "detail": str(exc),
            },
        )
    return {
        "bank_id": hindsight_integration.BANK_COMPETEIQ,
        "memories": items,
        "count": len(items),  # actual number returned by this API call (may be page-limited)
        "note": "count reflects the real API response for this request, not a total bank size",
    }


@router.get("/history")
def hindsight_history(db: Session = Depends(get_db)):
    """Historical decision timeline from the CompeteIQ database.

    Joins stored HindsightMemory workflow records and unified workflow runs
    (with their real memory references) against intelligence events so the UI
    can show which decision came from which historical memories.
    """
    workflows = (
        db.query(models.WorkflowRun)
        .order_by(models.WorkflowRun.created_at.desc())
        .limit(50)
        .all()
    )
    events = {e.id: e for e in db.query(models.IntelligenceEvent).all()}
    timeline = []
    for run in workflows:
        event = events.get(run.event_id)
        timeline.append(
            {
                "workflow_id": run.id,
                "event_id": run.event_id,
                "event_title": event.title if event else "",
                "event_company": event.company if event else "",
                "recall_count": run.hindsight_recall_count,
                "recall_refs": run.hindsight_recall_refs or [],
                "reflection": (run.hindsight_reflection_text or "")[:1500],
                "retained_at": run.hindsight_retained_at,
                "retained_refs": run.hindsight_retained_refs or [],
                "status": run.status,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
            }
        )
    return {
        "bank_id": hindsight_integration.BANK_COMPETEIQ,
        "workflow_records_count": len(timeline),
        "timeline": timeline,
    }


@router.post("/workflow/{event_id}")
async def hindsight_workflow(event_id: str, db: Session = Depends(get_db)):
    """Run the full Hindsight workflow for an intelligence event.

    Retrieves historical context, generates a recommendation, and persists
    memory records + a strategic recommendation to the CompeteIQ database.
    """
    event = db.query(models.IntelligenceEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Intelligence event not found")

    event_dict = {
        "id": event.id,
        "title": event.title,
        "company": event.company,
        "category": event.category,
        "description": event.description,
    }

    try:
        result = await _run_hindsight_workflow_async(event_dict)
    except RuntimeError as exc:
        status = hindsight_integration.status()
        raise HTTPException(
            status_code=502 if status.available else 503,
            detail={
                "error": "Hindsight workflow failed",
                "reason": status.reason,
                "setup_instructions": status.setup_instructions,
                "detail": str(exc),
            },
        )

    # Persist the Hindsight memory record to CompeteIQ database
    memory = models.HindsightMemory(
        event_id=event_id,
        title=event.title,
        summary=event.description,
        historical_events=[m.get("content", "") for m in result.get("historical_events", [])],
        previous_decisions=result.get("previous_decisions_summary", ""),
        previous_outcomes=result.get("previous_outcomes_summary", ""),
        similarities=result.get("similarities", ""),
        differences=result.get("differences", ""),
        recommended_action=result.get("recommended_action", ""),
        priority=result.get("priority", "medium"),
        confidence=result.get("confidence", "medium"),
        expected_impact=result.get("expected_impact", ""),
        evidence=result.get("evidence", [""])[0] if result.get("evidence") else "",
        memory_influence=result.get("memory_influence", ""),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    # Also create a strategic recommendation record
    recommendation = models.StrategicRecommendation(
        event_id=event_id,
        workflow_type="hindsight",
        event_summary=event.title,
        competitor_comparison=result.get("differences", ""),
        impact_on_nexora=event.impact_on_nexora or "",
        historical_context=result.get("memory_influence", ""),
        market_opportunity=result.get("strategic_opportunities", ""),
        competitive_threats=result.get("risks", ""),
        strengths_weaknesses="",
        recommended_strategy=result.get("recommended_action", ""),
        immediate_actions="",
        actions_30_day="",
        actions_90_day="",
        expected_business_impact=result.get("expected_impact", ""),
        risks_assumptions=result.get("risks", ""),
        evidence_sources=event.source_url or "",
        confidence_score=result.get("confidence", "medium"),
        status="pending",
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return {
        "memory_id": memory.id,
        "recommendation_id": recommendation.id,
        "workflow": "hindsight",
        "historical_events_count": len(result.get("historical_events", [])),
        "recommended_action": result.get("recommended_action", ""),
        "priority": result.get("priority", "medium"),
        "confidence": result.get("confidence", "medium"),
        "hindsight_available": True,
    }


async def _run_hindsight_workflow_async(event: dict) -> dict:
    """Run the full Hindsight workflow using async SDK methods."""
    title = event.get("title", "")
    company = event.get("company", "")
    description = event.get("description", "")
    category = event.get("category", "")
    event_id = event.get("id", "")

    # 1. Recall relevant historical events
    historical_events = await hindsight_integration.arecall(
        query=f"{title} {description} {company} {category}",
        bank_id=hindsight_integration.BANK_COMPETEIQ,
        limit=10,
    )

    # Build context from retrieved memories
    context_parts = []
    for m in historical_events:
        context_parts.append(f"- {m['content'][:300]}")
    historical_context = "\n".join(context_parts) if context_parts else "No prior memories found."

    # 2. Reflect to generate a recommendation
    reflection_query = (
        f"Current competitor event: {title} ({company}, {category})\n"
        f"Description: {description}\n\n"
        f"Historical memories from CompeteIQ:\n{historical_context}\n\n"
        "Generate a strategic recommendation for NEXORA AI based on this "
        "competitor event and the historical memories above. Identify "
        "similarities, differences, risks, opportunities, and a recommended "
        "action with priority and confidence."
    )
    reflection = await hindsight_integration.areflect(
        query=reflection_query,
        bank_id=hindsight_integration.BANK_COMPETEIQ,
    )

    # 3. Retain the current event as a new historical memory
    await hindsight_integration.aretain(
        content=(
            f"Competitor event: {title}\n"
            f"Company: {company}\n"
            f"Category: {category}\n"
            f"Description: {description}"
        ),
        bank_id=hindsight_integration.BANK_COMPETEIQ,
        metadata={
            "source": "competeiq-trending-event",
            "company": company,
            "category": category,
            "event_id": event_id,
            "type": "competitor_event",
        },
        context="competeiq-intelligence",
    )

    # 4. Retain the generated recommendation as a strategy memory
    await hindsight_integration.aretain(
        content=(
            f"Strategic recommendation for event '{title}' ({company}):\n"
            f"{reflection['reflection']}"
        ),
        bank_id=hindsight_integration.BANK_COMPETEIQ,
        metadata={
            "source": "competeiq-strategy",
            "company": company,
            "category": category,
            "event_id": event_id,
            "type": "strategic_recommendation",
        },
        context="competeiq-strategy",
    )

    return {
        "current_event": event,
        "historical_events": historical_events,
        "historical_events_count": len(historical_events),
        "historical_context": historical_context,
        "recommended_action": reflection["reflection"],
        "priority": "medium",
        "confidence": "medium",
        "evidence": [m["content"][:200] for m in historical_events[:3]],
        "expected_impact": "Strategic recommendation based on Hindsight historical memory.",
        "memory_influence": f"Retrieved {len(historical_events)} historical memories from Hindsight bank '{hindsight_integration.BANK_COMPETEIQ}'.",
        "retained_event": True,
        "retained_recommendation": True,
        "hindsight_available": True,
    }
