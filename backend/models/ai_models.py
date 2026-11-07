"""AI model intelligence models.

Tracks AI models — both NEXORA's own models and competitor models — with full
technical, commercial and competitive comparison data. Nothing is fabricated;
missing fields show as "Not publicly disclosed".
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AIModel(Base):
    """A single AI model record."""

    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identity
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    family: Mapped[str] = mapped_column(String, default="")
    version: Mapped[str] = mapped_column(String, default="")
    company: Mapped[str] = mapped_column(String, nullable=False, index=True)  # developer
    release_date: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="")  # Active, Development, Planned, Deprecated
    model_type: Mapped[str] = mapped_column(String, default="")  # e.g. Large Language Model, Vision Model

    # Technical specifications
    parameters: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    context_window: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    input_modalities: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    output_modalities: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    supported_languages: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    max_output_length: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    architecture: Mapped[str] = mapped_column(String, default="Not publicly disclosed")

    # Performance
    benchmark_scores: Mapped[dict] = mapped_column(JSON, default=dict)  # {benchmark_name: {score, date}}
    inference_speed: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    latency: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    throughput: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    reasoning_capabilities: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    coding_capabilities: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    vision_multimodal_capabilities: Mapped[str] = mapped_column(String, default="Not publicly disclosed")

    # Capacity and deployment
    gpu_requirements: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    vram_requirements: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    api_available: Mapped[bool] = mapped_column(Boolean, default=False)
    deployment: Mapped[str] = mapped_column(String, default="Not publicly disclosed")  # API / local / cloud
    quantization_options: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    compute_requirements: Mapped[str] = mapped_column(String, default="Not publicly disclosed")

    # Commercial
    input_pricing: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    output_pricing: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    subscription_plans: Mapped[str] = mapped_column(String, default="Not publicly disclosed")
    enterprise_available: Mapped[bool] = mapped_column(Boolean, default=False)
    license: Mapped[str] = mapped_column(String, default="Not publicly disclosed")

    # Metadata
    model_category: Mapped[str] = mapped_column(String, default="")
    source_url: Mapped[str] = mapped_column(String, default="")
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)  # official spec vs third-party vs estimated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
