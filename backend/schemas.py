"""Pydantic schemas for CompeteIQ API request/response validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


# ---------- Company ----------
class CompanySectionBase(BaseModel):
    section_id: str
    title: str
    data: Dict[str, Any] = {}
    is_sample: bool = False


class CompanySectionCreate(CompanySectionBase):
    pass


class CompanySectionUpdate(BaseModel):
    title: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_sample: Optional[bool] = None


class CompanySectionOut(CompanySectionBase):
    id: str
    company_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyBase(BaseModel):
    name: str
    description: str = ""
    website: str = ""
    contact_email: str = ""


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None


class CompanyOut(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyProfileOut(BaseModel):
    """Full company profile with all sections."""
    id: str
    name: str
    description: str
    website: str
    contact_email: str
    sections: List[CompanySectionOut] = []
    completeness: Dict[str, Any] = {}

    model_config = {"from_attributes": True}


# ---------- AI Models ----------
class AIModelBase(BaseModel):
    name: str
    family: str = ""
    version: str = ""
    company: str
    release_date: str = ""
    status: str = ""
    model_type: str = ""
    parameters: str = "Not publicly disclosed"
    context_window: str = "Not publicly disclosed"
    input_modalities: str = "Not publicly disclosed"
    output_modalities: str = "Not publicly disclosed"
    supported_languages: str = "Not publicly disclosed"
    max_output_length: str = "Not publicly disclosed"
    architecture: str = "Not publicly disclosed"
    benchmark_scores: Dict[str, Any] = {}
    inference_speed: str = "Not publicly disclosed"
    latency: str = "Not publicly disclosed"
    throughput: str = "Not publicly disclosed"
    reasoning_capabilities: str = "Not publicly disclosed"
    coding_capabilities: str = "Not publicly disclosed"
    vision_multimodal_capabilities: str = "Not publicly disclosed"
    gpu_requirements: str = "Not publicly disclosed"
    vram_requirements: str = "Not publicly disclosed"
    api_available: bool = False
    deployment: str = "Not publicly disclosed"
    quantization_options: str = "Not publicly disclosed"
    compute_requirements: str = "Not publicly disclosed"
    input_pricing: str = "Not publicly disclosed"
    output_pricing: str = "Not publicly disclosed"
    subscription_plans: str = "Not publicly disclosed"
    enterprise_available: bool = False
    license: str = "Not publicly disclosed"
    model_category: str = ""
    source_url: str = ""
    is_official: bool = False


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    name: Optional[str] = None
    family: Optional[str] = None
    version: Optional[str] = None
    company: Optional[str] = None
    release_date: Optional[str] = None
    status: Optional[str] = None
    model_type: Optional[str] = None
    parameters: Optional[str] = None
    context_window: Optional[str] = None
    input_modalities: Optional[str] = None
    output_modalities: Optional[str] = None
    supported_languages: Optional[str] = None
    max_output_length: Optional[str] = None
    architecture: Optional[str] = None
    benchmark_scores: Optional[Dict[str, Any]] = None
    inference_speed: Optional[str] = None
    latency: Optional[str] = None
    throughput: Optional[str] = None
    reasoning_capabilities: Optional[str] = None
    coding_capabilities: Optional[str] = None
    vision_multimodal_capabilities: Optional[str] = None
    gpu_requirements: Optional[str] = None
    vram_requirements: Optional[str] = None
    api_available: Optional[bool] = None
    deployment: Optional[str] = None
    quantization_options: Optional[str] = None
    compute_requirements: Optional[str] = None
    input_pricing: Optional[str] = None
    output_pricing: Optional[str] = None
    subscription_plans: Optional[str] = None
    enterprise_available: Optional[bool] = None
    license: Optional[str] = None
    model_category: Optional[str] = None
    source_url: Optional[str] = None
    is_official: Optional[bool] = None


class AIModelOut(AIModelBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Intelligence Events ----------
class IntelligenceEventBase(BaseModel):
    title: str
    company: str
    category: str
    description: str
    publication_date: str = ""
    source_url: str = ""
    evidence_snippet: str = ""
    confidence: str = "medium"
    event_type: str = "news"
    verification_status: str = "unverified"
    strategic_importance: str = "medium"
    impact_on_nexora: str = ""
    source_type: str = "public"
    demo_company_label: bool = False


class IntelligenceEventCreate(IntelligenceEventBase):
    pass


class IntelligenceEventUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    evidence_snippet: Optional[str] = None
    confidence: Optional[str] = None
    event_type: Optional[str] = None
    verification_status: Optional[str] = None
    strategic_importance: Optional[str] = None
    impact_on_nexora: Optional[str] = None
    source_type: Optional[str] = None
    demo_company_label: Optional[bool] = None


class IntelligenceEventOut(IntelligenceEventBase):
    id: str
    collection_date: datetime

    model_config = {"from_attributes": True}


# ---------- Demo Company ----------
class DemoCompanyUpdateIn(BaseModel):
    """Payload accepted from the external MINTY-GPT website."""
    company_name: Optional[str] = "MINTY-GPT"
    company_description: Optional[str] = ""
    model_updates: Optional[str] = ""
    product_updates: Optional[str] = ""
    pricing_updates: Optional[str] = ""
    infrastructure_updates: Optional[str] = ""
    business_strategy_updates: Optional[str] = ""
    event_title: Optional[str] = ""
    event_description: Optional[str] = ""
    event_category: Optional[str] = ""
    publication_date: Optional[str] = ""
    source_url: Optional[str] = ""
    change_type: Optional[str] = ""


class DemoCompanyOut(BaseModel):
    id: str
    company_name: str
    description: str
    model_updates: str
    product_updates: str
    pricing_updates: str
    infrastructure_updates: str
    business_strategy_updates: str
    is_simulated: bool
    last_updated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DemoCompanyUpdateOut(BaseModel):
    id: str
    demo_company_id: str
    company_name: str
    company_description: str
    model_updates: str
    product_updates: str
    pricing_updates: str
    infrastructure_updates: str
    business_strategy_updates: str
    event_title: str
    event_description: str
    event_category: str
    publication_date: str
    source_url: str
    change_type: str
    changed_fields: List[str] = []
    received_at: datetime
    created_intelligence_event: bool

    model_config = {"from_attributes": True}


# ---------- Strategic Recommendation ----------
class StrategicRecommendationOut(BaseModel):
    id: str
    event_id: str
    workflow_type: str
    event_summary: str
    competitor_comparison: str
    impact_on_nexora: str
    impact_on_minty: str
    historical_context: str
    market_opportunity: str
    competitive_threats: str
    strengths_weaknesses: str
    recommended_strategy: str
    immediate_actions: str
    actions_30_day: str
    actions_90_day: str
    expected_business_impact: str
    risks_assumptions: str
    evidence_sources: str
    confidence_score: str
    status: str
    action_taken: str
    outcome_recorded: str
    created_at: datetime
    updated_at: datetime
    workflow_id: str = ""
    band_room_id: str = ""
    band_room_url: str = ""
    hindsight_memory_refs: List[Any] = []
    hindsight_retained_at: str = ""

    model_config = {"from_attributes": True}


class StrategicRecommendationUpdate(BaseModel):
    status: Optional[str] = None
    action_taken: Optional[str] = None
    outcome_recorded: Optional[str] = None


# ---------- Agent Message ----------
class AgentMessageOut(BaseModel):
    id: str
    recommendation_id: str
    agent_name: str
    agent_role: str
    task: str
    status: str
    message: str
    output: str
    timestamp: datetime
    handoff_to: str
    workflow_id: str = ""
    band_message_id: str = ""
    band_sent_at: str = ""
    sender_name: str = ""
    direction: str = "dispatch"

    model_config = {"from_attributes": True}


# ---------- Unified Workflow Runs ----------
class WorkflowStageOut(BaseModel):
    stage: str
    status: str
    detail: str = ""
    error: str = ""
    at: str = ""


class WorkflowRunOut(BaseModel):
    """A unified workflow run across CompeteIQ, BAND and Hindsight."""

    id: str
    event_id: str
    recommendation_id: str
    band_room_id: str = ""
    band_room_title: str = ""
    band_room_url: str = ""
    event_published_message_id: str = ""
    strategy_final_message_id: str = ""
    hindsight_recall_refs: List[Any] = []
    hindsight_recall_count: int = 0
    hindsight_reflection_text: str = ""
    hindsight_retained_refs: List[Any] = []
    hindsight_retained_at: str = ""
    status: str = "running"
    stages: List[Any] = []
    error: str = ""
    started_at: datetime
    completed_at: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


class BandRoomMessageOut(BaseModel):
    """A real message delivered through the BAND room."""

    id: str
    sender_id: str
    sender_name: str = ""
    sender_type: str = ""
    message_type: str = ""
    content: str = ""
    created_at: str = ""
    updated_at: str = ""


# ---------- Collection Job ----------
class CollectionJobOut(BaseModel):
    id: str
    source_name: str
    source_type: str
    status: str
    events_collected: int
    error_message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_updated: str

    model_config = {"from_attributes": True}


# ---------- Dashboard ----------
class DashboardStats(BaseModel):
    companies_monitored: int
    latest_events: int
    ai_models_tracked: int
    profile_completion: int
    minty_updates: int
    hindsight_status: str
    band_status: str
    recent_recommendations: int
    threats: int
    opportunities: int
    last_updated: str


# ---------- Hindsight Memory ----------
class HindsightRecallIn(BaseModel):
    query: str
    bank_id: str = "competeiq-intelligence"
    limit: int = 10
    budget: str = "mid"


class HindsightRetainIn(BaseModel):
    content: str
    bank_id: str = "competeiq-intelligence"
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[str] = None


class HindsightReflectIn(BaseModel):
    query: str
    bank_id: str = "competeiq-intelligence"
    budget: str = "mid"
    context: Optional[str] = None


class HindsightStatusOut(BaseModel):
    configured: bool
    available: bool
    reason: str
    banks: List[str] = []
    setup_instructions: List[str] = []
    version: Optional[str] = None


# ---------- BAND AI ----------
class BandMessageIn(BaseModel):
    agent_name: str
    message: str
    task: str = ""
    handoff_to: Optional[str] = None
    recommendation_id: Optional[str] = None


class WorkflowFinalizeIn(BaseModel):
    """Optional user feedback recorded with the retained Hindsight experience."""
    user_feedback: str = ""
    outcome: str = ""

