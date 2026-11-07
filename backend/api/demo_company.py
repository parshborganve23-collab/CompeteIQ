"""API routes for MINTY-GPT (simulated demo company) integration.

Endpoints:
  POST   /api/demo-company/update   - external website sends updates
  GET    /api/demo-company          - latest MINTY-GPT profile
  GET    /api/demo-company/events   - update history

Authentication: configurable API key sent as X-Demo-API-Key header.
"""
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["Demo Company (MINTY-GPT)"])

DEMO_API_KEY = os.getenv("DEMO_COMPANY_API_KEY", "")


def verify_api_key(x_demo_api_key: str = Header(default="")):
    """Validate the demo company API key. Returns True if valid or not configured."""
    if not DEMO_API_KEY:
        # Not configured: allow but this should be set in production
        return True
    if x_demo_api_key != DEMO_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing demo company API key",
        )
    return True


def _ensure_demo_company(db: Session) -> models.DemoCompany:
    dc = db.query(models.DemoCompany).first()
    if not dc:
        dc = models.DemoCompany(
            company_name="MINTY-GPT",
            description="",
            is_simulated=True,
        )
        db.add(dc)
        db.commit()
        db.refresh(dc)
    return dc


def _detect_changed_fields(prev: models.DemoCompany, payload: schemas.DemoCompanyUpdateIn) -> List[str]:
    """Detect which profile fields changed vs the previous stored state."""
    changed: List[str] = []
    fields = [
        ("company_name", payload.company_name),
        ("company_description", payload.company_description),
        ("model_updates", payload.model_updates),
        ("product_updates", payload.product_updates),
        ("pricing_updates", payload.pricing_updates),
        ("infrastructure_updates", payload.infrastructure_updates),
        ("business_strategy_updates", payload.business_strategy_updates),
    ]
    for field, value in fields:
        current = getattr(prev, field, "") or ""
        incoming = value or ""
        if current != incoming:
            changed.append(field)
    return changed


@router.post("/update", response_model=schemas.DemoCompanyUpdateOut)
def receive_update(
    payload: schemas.DemoCompanyUpdateIn,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
):
    """Receive an update from the external MINTY-GPT website.

    Stores the update, detects changed fields, and creates a new intelligence
    event when meaningful changes occur.
    """
    demo = _ensure_demo_company(db)

    # Detect changes vs previous state
    changed_fields = _detect_changed_fields(demo, payload)

    # Store the update record
    update_record = models.DemoCompanyUpdate(
        demo_company_id=demo.id,
        company_name=payload.company_name or "",
        company_description=payload.company_description or "",
        model_updates=payload.model_updates or "",
        product_updates=payload.product_updates or "",
        pricing_updates=payload.pricing_updates or "",
        infrastructure_updates=payload.infrastructure_updates or "",
        business_strategy_updates=payload.business_strategy_updates or "",
        event_title=payload.event_title or "",
        event_description=payload.event_description or "",
        event_category=payload.event_category or "",
        publication_date=payload.publication_date or "",
        source_url=payload.source_url or "",
        change_type=payload.change_type or "",
        changed_fields=changed_fields,
    )
    db.add(update_record)

    # Update the latest demo company state
    demo.company_name = payload.company_name or demo.company_name
    demo.description = payload.company_description or demo.description
    demo.model_updates = payload.model_updates or demo.model_updates
    demo.product_updates = payload.product_updates or demo.product_updates
    demo.pricing_updates = payload.pricing_updates or demo.pricing_updates
    demo.infrastructure_updates = payload.infrastructure_updates or demo.infrastructure_updates
    demo.business_strategy_updates = payload.business_strategy_updates or demo.business_strategy_updates

    # Create a new intelligence event when meaningful changes occur
    created_event = False
    if changed_fields and payload.event_title:
        event = models.IntelligenceEvent(
            title=payload.event_title,
            company=demo.company_name or "MINTY-GPT",
            category=payload.event_category or "products",
            description=payload.event_description or "",
            publication_date=payload.publication_date or "",
            source_url=payload.source_url or "",
            evidence_snippet=(payload.event_description or "")[:300],
            confidence="medium",
            event_type="demo-api",
            verification_status="unverified",
            strategic_importance="medium",
            impact_on_nexora="",
            source_type="demo-api",
            demo_company_label=True,
        )
        db.add(event)
        db.flush()  # get event id
        update_record.created_intelligence_event = True
        created_event = True

    db.commit()
    db.refresh(update_record)

    return schemas.DemoCompanyUpdateOut.model_validate(update_record)


@router.get("/", response_model=schemas.DemoCompanyOut)
def get_demo_company(db: Session = Depends(get_db)):
    """Get the latest MINTY-GPT simulated company profile."""
    demo = _ensure_demo_company(db)
    return demo


@router.get("/events", response_model=List[schemas.DemoCompanyUpdateOut])
def get_demo_events(db: Session = Depends(get_db)):
    """Get the MINTY-GPT update history."""
    demo = _ensure_demo_company(db)
    return (
        db.query(models.DemoCompanyUpdate)
        .filter_by(demo_company_id=demo.id)
        .order_by(models.DemoCompanyUpdate.received_at.desc())
        .all()
    )
