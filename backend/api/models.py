"""API routes for AI model intelligence."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["AI Models"])


@router.get("/", response_model=List[schemas.AIModelOut])
def list_models(
    db: Session = Depends(get_db),
    company: Optional[str] = Query(None, description="Filter by developer company"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by model category"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List AI models with optional filters."""
    q = db.query(models.AIModel)
    if company:
        q = q.filter(models.AIModel.company == company)
    if status:
        q = q.filter(models.AIModel.status == status)
    if category:
        q = q.filter(models.AIModel.model_category == category)
    return q.offset(offset).limit(limit).all()


@router.get("/{model_id}", response_model=schemas.AIModelOut)
def get_model(model_id: str, db: Session = Depends(get_db)):
    """Get a single AI model by ID (detail view)."""
    model = db.query(models.AIModel).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return model


@router.post("/", response_model=schemas.AIModelOut)
def create_model(payload: schemas.AIModelCreate, db: Session = Depends(get_db)):
    """Create a new AI model record."""
    model = models.AIModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.patch("/{model_id}", response_model=schemas.AIModelOut)
def update_model(model_id: str, payload: schemas.AIModelUpdate, db: Session = Depends(get_db)):
    """Update an AI model record."""
    model = db.query(models.AIModel).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="AI model not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    """Delete an AI model record."""
    model = db.query(models.AIModel).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="AI model not found")
    db.delete(model)
    db.commit()
    return {"ok": True, "message": "AI model deleted"}
