"""Base collector class for the intelligence collection pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class CollectorResult:
    """Outcome of a collection run."""
    source_name: str
    source_type: str
    status: str = "pending"  # pending, running, completed, failed
    events: List[dict] = field(default_factory=list)
    error_message: str = ""
    collected_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def mark_started(self):
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, events: List[dict]):
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.events = events
        self.collected_count = len(events)

    def mark_failed(self, error_message: str):
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message

    def last_updated(self) -> str:
        if self.completed_at:
            return self.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if self.started_at:
            return self.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        return "Not started"


class BaseCollector(ABC):
    """Base class for all intelligence data collectors."""

    def __init__(self, source_name: str, source_type: str = "public"):
        self.source_name = source_name
        self.source_type = source_type

    @abstractmethod
    def collect(self) -> CollectorResult:
        """Poll the source and return a CollectorResult with discovered events."""
        raise NotImplementedError

    def _event(self, title: str, company: str, category: str, description: str,
               source_url: str, publication_date: str = "",
               evidence_snippet: str = "", confidence: str = "medium",
               event_type: str = "news", verification_status: str = "unverified",
               strategic_importance: str = "medium", impact_on_nexora: str = "",
               demo_company_label: bool = False) -> dict:
        """Build a normalized event dict."""
        now = datetime.now(timezone.utc)
        return {
            "title": title,
            "company": company,
            "category": category,
            "description": description,
            "publication_date": publication_date,
            "collection_date": now,
            "source_url": source_url,
            "evidence_snippet": evidence_snippet or description[:300],
            "confidence": confidence,
            "event_type": event_type,
            "verification_status": verification_status,
            "strategic_importance": strategic_importance,
            "impact_on_nexora": impact_on_nexora,
            "source_type": self.source_type,
            "demo_company_label": demo_company_label,
        }
