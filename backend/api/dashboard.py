"""API routes for the dashboard overview."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Compute dashboard metrics from actual database data."""
    companies_monitored = db.query(models.IntelligenceEvent.company).distinct().count()
    latest_events = db.query(models.IntelligenceEvent).count()
    ai_models_tracked = db.query(models.AIModel).count()

    # Company profile completion
    company = db.query(models.Company).first()
    profile_completion = 0
    if company:
        sections = db.query(models.CompanySection).filter_by(company_id=company.id).all()
        total = len(sections) or 1
        filled = sum(1 for s in sections if s.data and any(str(v).strip() for v in s.data.values()))
        profile_completion = round((filled / total) * 100)

    minty_updates = db.query(models.DemoCompanyUpdate).count()
    recent_recommendations = db.query(models.StrategicRecommendation).count()
    threats = (
        db.query(models.IntelligenceEvent)
        .filter(models.IntelligenceEvent.strategic_importance.in_(["high", "critical"]))
        .count()
    )

    # Integration status (real, based on env config)
    hindsight_status = "configured" if __import__("os").getenv("HINDSIGHT_API_URL") else "not configured"
    band_status = "configured" if __import__("os").getenv("BAND_AI_API_URL") else "not configured"

    # Last updated = most recent event collection or demo update
    last_event = (
        db.query(models.IntelligenceEvent)
        .order_by(models.IntelligenceEvent.collection_date.desc())
        .first()
    )
    last_updated = last_event.collection_date.isoformat() if last_event else "Never"

    return schemas.DashboardStats(
        companies_monitored=companies_monitored,
        latest_events=latest_events,
        ai_models_tracked=ai_models_tracked,
        profile_completion=profile_completion,
        minty_updates=minty_updates,
        hindsight_status=hindsight_status,
        band_status=band_status,
        recent_recommendations=recent_recommendations,
        threats=threats,
        opportunities=latest_events,  # derive from events as opportunities
        last_updated=last_updated,
    )
