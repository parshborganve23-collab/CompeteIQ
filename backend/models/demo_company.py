"""Demo company (MINTY-GPT) integration models.

Stores MINTY-GPT profile updates received from an external website via API.
Maintains an update history, detects changed fields, and creates intelligence
events when meaningful changes occur. Always labeled as a simulated demo company.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class DemoCompany(Base):
    """MINTY-GPT simulated company profile — latest received state."""

    __tablename__ = "demo_companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name: Mapped[str] = mapped_column(String, nullable=False, default="MINTY-GPT")
    description: Mapped[str] = mapped_column(Text, default="")
    model_updates: Mapped[str] = mapped_column(Text, default="")
    product_updates: Mapped[str] = mapped_column(Text, default="")
    pricing_updates: Mapped[str] = mapped_column(Text, default="")
    infrastructure_updates: Mapped[str] = mapped_column(Text, default="")
    business_strategy_updates: Mapped[str] = mapped_column(Text, default="")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updates = relationship("DemoCompanyUpdate", back_populates="demo_company", cascade="all, delete-orphan")


class DemoCompanyUpdate(Base):
    """One update received from the external MINTY-GPT website."""

    __tablename__ = "demo_company_updates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    demo_company_id: Mapped[str] = mapped_column(String, ForeignKey("demo_companies.id"), index=True)

    # Accepted fields
    company_name: Mapped[str] = mapped_column(String, default="")
    company_description: Mapped[str] = mapped_column(Text, default="")
    model_updates: Mapped[str] = mapped_column(Text, default="")
    product_updates: Mapped[str] = mapped_column(Text, default="")
    pricing_updates: Mapped[str] = mapped_column(Text, default="")
    infrastructure_updates: Mapped[str] = mapped_column(Text, default="")
    business_strategy_updates: Mapped[str] = mapped_column(Text, default="")

    # Intelligence event fields
    event_title: Mapped[str] = mapped_column(String, default="")
    event_description: Mapped[str] = mapped_column(Text, default="")
    event_category: Mapped[str] = mapped_column(String, default="")
    publication_date: Mapped[str] = mapped_column(String, default="")
    source_url: Mapped[str] = mapped_column(String, default="")
    change_type: Mapped[str] = mapped_column(String, default="")

    changed_fields: Mapped[list] = mapped_column(JSON, default=list)  # fields that changed vs previous
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_intelligence_event: Mapped[bool] = mapped_column(Boolean, default=False)

    demo_company = relationship("DemoCompany", back_populates="updates")
