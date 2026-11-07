"""API routes for intelligence events (trending feed)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["Intelligence Events"])


@router.get("/", response_model=List[schemas.IntelligenceEventOut])
def list_events(
    db: Session = Depends(get_db),
    company: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    demo_only: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List intelligence events with filters for the trending feed."""
    q = db.query(models.IntelligenceEvent)
    if company:
        q = q.filter(models.IntelligenceEvent.company == company)
    if category:
        q = q.filter(models.IntelligenceEvent.category == category)
    if source_type:
        q = q.filter(models.IntelligenceEvent.source_type == source_type)
    if verification_status:
        q = q.filter(models.IntelligenceEvent.verification_status == verification_status)
    if demo_only is True:
        q = q.filter(models.IntelligenceEvent.demo_company_label == True)  # noqa: E712
    elif demo_only is False:
        q = q.filter(models.IntelligenceEvent.demo_company_label != True)  # noqa: E712
    # newest first
    q = q.order_by(models.IntelligenceEvent.collection_date.desc())
    return q.offset(offset).limit(limit).all()


@router.get("/{event_id}", response_model=schemas.IntelligenceEventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Get a single intelligence event."""
    event = db.query(models.IntelligenceEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Intelligence event not found")
    return event


@router.post("/", response_model=schemas.IntelligenceEventOut)
def create_event(payload: schemas.IntelligenceEventCreate, db: Session = Depends(get_db)):
    """Create a new intelligence event."""
    event = models.IntelligenceEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=schemas.IntelligenceEventOut)
def update_event(event_id: str, payload: schemas.IntelligenceEventUpdate, db: Session = Depends(get_db)):
    """Update an intelligence event."""
    event = db.query(models.IntelligenceEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Intelligence event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """Delete an intelligence event."""
    event = db.query(models.IntelligenceEvent).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Intelligence event not found")
    db.delete(event)
    db.commit()
    return {"ok": True, "message": "Intelligence event deleted"}
