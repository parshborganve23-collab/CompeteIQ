"""Background collection jobs.

Runs registered collectors, persists IntelligenceEvent records to the
database, and records CollectionJob runs. Collection is periodic and triggered
manually or by a scheduler — never claimed to be real-time.
"""
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database import SessionLocal, init_db
import models
from collectors import collector_registry, get_collector, list_collectors, register
from collectors.newsroom import (
    NewsroomCollector, HuggingFaceCollector, ArxivCollector, GitHubCollector,
)


def register_default_collectors():
    """Register collectors for all monitored AI companies and public sources."""
    registry = collector_registry()
    companies = [
        "OpenAI", "Google DeepMind", "Anthropic", "Microsoft AI", "Meta AI",
        "NVIDIA", "xAI", "Mistral AI", "DeepSeek", "Amazon AWS AI",
    ]
    for company in companies:
        if company not in registry:
            register(NewsroomCollector(company))
    github_token = os.getenv("GITHUB_TOKEN") or None
    if "Hugging Face" not in registry:
        register(HuggingFaceCollector())
    if "arXiv" not in registry:
        register(ArxivCollector())
    if "GitHub" not in registry:
        register(GitHubCollector(token=github_token))


def run_collector(source_name: str, db: Session) -> models.CollectionJob:
    """Run a single collector and store results. Returns the job record."""
    job = models.CollectionJob(
        source_name=source_name,
        source_type="public",
        status="running",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    register_default_collectors()
    collector = get_collector(source_name)

    if collector is None:
        job.status = "failed"
        job.error_message = f"No collector registered for '{source_name}'"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        return job

    try:
        result = collector.collect()
        job.source_type = result.source_type
        job.last_updated = result.last_updated()

        # Deduplicate by title + company + source_url before inserting
        existing = {
            (e.title, e.company, e.source_url)
            for e in db.query(models.IntelligenceEvent).all()
        }

        stored = 0
        for ev in result.events:
            key = (ev["title"], ev["company"], ev["source_url"])
            if key in existing:
                continue
            event = models.IntelligenceEvent(**ev)
            db.add(event)
            stored += 1

        job.events_collected = stored
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return job


def run_all_collectors() -> list:
    """Run every registered collector. Returns list of job records."""
    init_db()
    register_default_collectors()
    db = SessionLocal()
    try:
        jobs = []
        for source_name in list_collectors():
            jobs.append(run_collector(source_name, db))
        return jobs
    finally:
        db.close()


def run_collector_sync(source_name: str) -> dict:
    """Convenience wrapper returning a serializable job summary."""
    init_db()
    db = SessionLocal()
    try:
        job = run_collector(source_name, db)
        return {
            "id": job.id,
            "source_name": job.source_name,
            "source_type": job.source_type,
            "status": job.status,
            "events_collected": job.events_collected,
            "error_message": job.error_message,
            "last_updated": job.last_updated,
        }
    finally:
        db.close()
