
"""CompeteIQ API router registration."""

from fastapi import APIRouter

from . import (
    band,
    collection,
    company,
    dashboard,
    demo_company,
    hindsight,
    intelligence,
    models as models_api,
    strategy,
    workflows,
)

api_router = APIRouter()

# Company Profile
api_router.include_router(company.router)

# AI Models
api_router.include_router(models_api.router, prefix="/models", tags=["AI Models"])

# Competitive Intelligence
api_router.include_router(
    intelligence.router,
    prefix="/intelligence",
    tags=["Intelligence Events"],
)

# Dashboard
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

# Hindsight Memory
api_router.include_router(
    hindsight.router,
    prefix="/hindsight",
    tags=["Hindsight Memory"],
)

# BAND AI Agents
api_router.include_router(
    band.router,
    prefix="/band",
    tags=["BAND AI Agents"],
)

# Simulated Demo Company
api_router.include_router(
    demo_company.router,
    prefix="/demo-company",
    tags=["Demo Company"],
)

# Strategy and Recommendations
api_router.include_router(
    strategy.router,
    prefix="/strategy",
    tags=["Strategy"],
)

# Unified Workflows (CompeteIQ + BAND + Hindsight)
api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["Unified Workflows"],
)

# Data Collection
api_router.include_router(
    collection.router,
    prefix="/collection",
    tags=["Data Collection"],
)
