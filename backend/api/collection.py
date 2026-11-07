"""API routes for data collection jobs (monitoring pipeline)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(tags=["Data Collection"])


@router.get("/sources")
def list_sources():
    """List available collection sources (registered collectors)."""
    import jobs  # noqa: WPS433
    jobs.register_default_collectors()
    from collectors import list_collectors
    return {"sources": list_collectors()}


@router.post("/run/{source_name}", response_model=schemas.CollectionJobOut)
def run_collector(source_name: str, db: Session = Depends(get_db)):
    """Manually trigger a collection job for a source (periodic, not real-time)."""
    import jobs  # noqa: WPS433
    return jobs.run_collector(source_name, db)


@router.post("/run-all")
def run_all_collectors():
    """Run every registered collector."""
    import jobs  # noqa: WPS433
    jobs.run_all_collectors()
    return {"ok": True, "message": "All collectors triggered"}


@router.get("/", response_model=List[schemas.CollectionJobOut])
def list_jobs(
    db: Session = Depends(get_db),
    source_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List collection jobs (monitoring pipeline runs)."""
    q = db.query(models.CollectionJob)
    if source_name:
        q = q.filter(models.CollectionJob.source_name == source_name)
    if status:
        q = q.filter(models.CollectionJob.status == status)
    return q.order_by(models.CollectionJob.started_at.desc()).offset(offset).limit(limit).all()


@router.get("/{job_id}", response_model=schemas.CollectionJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a single collection job."""
    job = db.query(models.CollectionJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")
    return job


@router.post("/", response_model=schemas.CollectionJobOut)
def create_job(
    source_name: str,
    source_type: str = "public",
    db: Session = Depends(get_db),
):
    """Create a new collection job."""
    job = models.CollectionJob(source_name=source_name, source_type=source_type, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.patch("/{job_id}", response_model=schemas.CollectionJobOut)
def update_job(
    job_id: str,
    status: Optional[str] = None,
    events_collected: Optional[int] = None,
    error_message: Optional[str] = None,
    last_updated: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update a collection job's status/results."""
    from datetime import datetime
    job = db.query(models.CollectionJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")
    if status is not None:
        job.status = status
    if events_collected is not None:
        job.events_collected = events_collected
    if error_message is not None:
        job.error_message = error_message
    if last_updated is not None:
        job.last_updated = last_updated
    if status in ("completed", "failed"):
        job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job
