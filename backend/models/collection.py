"""Data collection job models.

Tracks periodic monitoring jobs that poll public sources for AI company
intelligence. Collection is periodic, never claimed to be real-time.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CollectionJob(Base):
    """A single monitoring/collection job run."""

    __tablename__ = "collection_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String, nullable=False, index=True)  # e.g. "OpenAI Newsroom", "Hugging Face"
    source_type: Mapped[str] = mapped_column(String, default="public")  # newsroom, rss, github, huggingface, arxiv, demo-api
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, completed, failed
    events_collected: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[str] = mapped_column(String, default="")  # human-readable last updated time
