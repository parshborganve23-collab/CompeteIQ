"""Strategy and memory models.

Holds Hindsight memory records, BAND AI agent messages, strategic
recommendations produced by the intelligence workflows, and unified
workflow runs that tie CompeteIQ, BAND rooms and Hindsight together.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class HindsightMemory(Base):
    """A historical memory record retrieved/saved through Hindsight."""

    __tablename__ = "hindsight_memories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, index=True)  # related intelligence event
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    historical_events: Mapped[list] = mapped_column(JSON, default=list)  # retrieved historical event refs
    previous_decisions: Mapped[str] = mapped_column(Text, default="")
    previous_outcomes: Mapped[str] = mapped_column(Text, default="")
    similarities: Mapped[str] = mapped_column(Text, default="")
    differences: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String, default="medium")
    confidence: Mapped[str] = mapped_column(String, default="medium")
    expected_impact: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[str] = mapped_column(Text, default="")
    memory_influence: Mapped[str] = mapped_column(Text, default="")  # how history influenced the recommendation
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StrategicRecommendation(Base):
    """Final strategic report from Hindsight or BAND AI workflow."""

    __tablename__ = "strategic_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, index=True)
    workflow_type: Mapped[str] = mapped_column(String, default="")  # hindsight, band-ai, both
    event_summary: Mapped[str] = mapped_column(Text, default="")
    competitor_comparison: Mapped[str] = mapped_column(Text, default="")
    impact_on_nexora: Mapped[str] = mapped_column(Text, default="")
    impact_on_minty: Mapped[str] = mapped_column(Text, default="")
    historical_context: Mapped[str] = mapped_column(Text, default="")
    market_opportunity: Mapped[str] = mapped_column(Text, default="")
    competitive_threats: Mapped[str] = mapped_column(Text, default="")
    strengths_weaknesses: Mapped[str] = mapped_column(Text, default="")
    recommended_strategy: Mapped[str] = mapped_column(Text, default="")
    immediate_actions: Mapped[str] = mapped_column(Text, default="")
    actions_30_day: Mapped[str] = mapped_column(Text, default="")
    actions_90_day: Mapped[str] = mapped_column(Text, default="")
    expected_business_impact: Mapped[str] = mapped_column(Text, default="")
    risks_assumptions: Mapped[str] = mapped_column(Text, default="")
    evidence_sources: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[str] = mapped_column(String, default="medium")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, accepted, rejected
    action_taken: Mapped[str] = mapped_column(Text, default="")
    outcome_recorded: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ---- unified synchronization fields (added by safe migration) ----
    workflow_id: Mapped[str] = mapped_column(String, default="", index=True)
    band_room_id: Mapped[str] = mapped_column(String, default="")
    band_room_url: Mapped[str] = mapped_column(String, default="")
    hindsight_memory_refs: Mapped[list] = mapped_column(JSON, default=list)
    hindsight_retained_at: Mapped[str] = mapped_column(String, default="")


class AgentMessage(Base):
    """A message exchanged between BAND AI agents during a workflow."""

    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id: Mapped[str] = mapped_column(String, ForeignKey("strategic_recommendations.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_role: Mapped[str] = mapped_column(String, default="")
    task: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, completed, failed, waiting
    message: Mapped[str] = mapped_column(Text, default="")
    output: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    handoff_to: Mapped[str] = mapped_column(String, default="")  # next agent in the chain

    # ---- unified synchronization fields (added by safe migration) ----
    workflow_id: Mapped[str] = mapped_column(String, default="", index=True)
    band_message_id: Mapped[str] = mapped_column(String, default="")
    band_sent_at: Mapped[str] = mapped_column(String, default="")  # Band message created_at (ISO)
    sender_name: Mapped[str] = mapped_column(String, default="")
    direction: Mapped[str] = mapped_column(String, default="dispatch")  # dispatch, agent_reply, event_publish, final_recommendation


class WorkflowRun(Base):
    """A unified workflow run connecting CompeteIQ, a BAND room and Hindsight.

    Every analysis gets a unique workflow ID. The run records which stage of
    the cross-platform pipeline succeeded, the stored BAND room reference
    (to prevent duplicate rooms), the real BAND message IDs, and the real
    Hindsight memory references. Nothing here is fabricated: failed stages
    keep the ``error`` text from the real API response.
    """

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String, index=True)
    recommendation_id: Mapped[str] = mapped_column(String, default="", index=True)

    # BAND room reference — reused across runs of the same event.
    band_room_id: Mapped[str] = mapped_column(String, default="")
    band_room_title: Mapped[str] = mapped_column(String, default="")
    band_room_url: Mapped[str] = mapped_column(String, default="")
    event_published_message_id: Mapped[str] = mapped_column(String, default="")
    strategy_final_message_id: Mapped[str] = mapped_column(String, default="")

    # Hindsight references (real API results only).
    hindsight_recall_refs: Mapped[list] = mapped_column(JSON, default=list)  # [{id, content, score}]
    hindsight_recall_count: Mapped[int] = mapped_column(default=0)
    hindsight_reflection_text: Mapped[str] = mapped_column(Text, default="")
    hindsight_retained_refs: Mapped[list] = mapped_column(JSON, default=list)  # operation ids
    hindsight_retained_at: Mapped[str] = mapped_column(String, default="")

    status: Mapped[str] = mapped_column(String, default="running")  # running, dispatched, completed, partial, failed
    stages: Mapped[list] = mapped_column(JSON, default=list)  # [{stage, status, detail, error, at}]
    error: Mapped[str] = mapped_column(Text, default="")

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
