"""Intelligence event models.

Stores trending intelligence events collected from public sources, NEXORA AI,
and MINTY-GPT (simulated demo company). Events are never fabricated — every
event has a source URL, collection date, confidence and verification status.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class IntelligenceEvent(Base):
    """A single intelligence event (news, release, funding, partnership, etc.)."""

    __tablename__ = "intelligence_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False, index=True)  # OpenAI, Google, NEXORA AI, MINTY-GPT, etc.
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)  # models, pricing, research, funding, partnerships, infrastructure, products
    description: Mapped[str] = mapped_column(Text, nullable=False)
    publication_date: Mapped[str] = mapped_column(String, default="")  # original publication date (ISO string)
    collection_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_url: Mapped[str] = mapped_column(String, default="")
    evidence_snippet: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String, default="medium")  # low, medium, high
    event_type: Mapped[str] = mapped_column(String, default="news")  # news, report, estimate, unverified
    verification_status: Mapped[str] = mapped_column(String, default="unverified")  # verified, media, estimate, unverified
    strategic_importance: Mapped[str] = mapped_column(String, default="medium")  # low, medium, high, critical
    impact_on_nexora: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String, default="public")  # official, news, github, huggingface, arxiv, demo-api, other
    demo_company_label: Mapped[bool] = mapped_column(default=False)  # True if MINTY-GPT simulated event
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
