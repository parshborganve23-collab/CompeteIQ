"""Company profile models.

Stores NEXORA AI's company profile as sections (JSON), so each of the 14
sections can be added, edited, deleted and saved independently.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Company(Base):
    """Singleton company record — NEXORA AI is the comparison baseline."""

    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    website: Mapped[str] = mapped_column(String, default="")
    contact_email: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sections = relationship("CompanySection", back_populates="company", cascade="all, delete-orphan")


class CompanySection(Base):
    """One section of the company profile (e.g. overview, products, pricing)."""

    __tablename__ = "company_sections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), index=True)
    section_id: Mapped[str] = mapped_column(String, nullable=False, index=True)  # e.g. "overview", "products"
    title: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_sample: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    company = relationship("Company", back_populates="sections")
