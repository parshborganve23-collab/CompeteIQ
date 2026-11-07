"""API routes for strategic recommendations (Hindsight / BAND AI output)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["Strategy & Recommendations"])


@router.get("/", response_model=List[schemas.StrategicRecommendationOut])
def list_recommendations(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    workflow_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List strategic recommendations."""
    q = db.query(models.StrategicRecommendation)
    if status:
        q = q.filter(models.StrategicRecommendation.status == status)
    if workflow_type:
        q = q.filter(models.StrategicRecommendation.workflow_type == workflow_type)
    return q.order_by(models.StrategicRecommendation.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{rec_id}", response_model=schemas.StrategicRecommendationOut)
def get_recommendation(rec_id: str, db: Session = Depends(get_db)):
    """Get a single strategic recommendation."""
    rec = db.query(models.StrategicRecommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Strategic recommendation not found")
    return rec


@router.patch("/{rec_id}", response_model=schemas.StrategicRecommendationOut)
def update_recommendation(
    rec_id: str,
    payload: schemas.StrategicRecommendationUpdate,
    db: Session = Depends(get_db),
):
    """Accept/reject a recommendation and record action taken + outcome."""
    rec = db.query(models.StrategicRecommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Strategic recommendation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/{rec_id}/agents", response_model=List[schemas.AgentMessageOut])
def get_agent_messages(rec_id: str, db: Session = Depends(get_db)):
    """Get BAND AI agent messages for a recommendation."""
    rec = db.query(models.StrategicRecommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Strategic recommendation not found")
    return (
        db.query(models.AgentMessage)
        .filter_by(recommendation_id=rec_id)
        .order_by(models.AgentMessage.timestamp.asc())
        .all()
    )


@router.post("/{rec_id}/agents", response_model=schemas.AgentMessageOut)
def add_agent_message(
    rec_id: str,
    agent_name: str,
    agent_role: str = "",
    task: str = "",
    status: str = "pending",
    message: str = "",
    output: str = "",
    handoff_to: str = "",
    db: Session = Depends(get_db),
):
    """Add an agent message (used by BAND AI workflow integration)."""
    rec = db.query(models.StrategicRecommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Strategic recommendation not found")
    msg = models.AgentMessage(
        recommendation_id=rec_id,
        agent_name=agent_name,
        agent_role=agent_role,
        task=task,
        status=status,
        message=message,
        output=output,
        handoff_to=handoff_to,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
