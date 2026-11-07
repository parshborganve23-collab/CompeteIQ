"""CompeteIQ FastAPI application."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env before reading CORS or creating integrations.
load_dotenv(Path(__file__).resolve().parent / ".env")

from api import api_router  # noqa: E402
from integrations import band_integration, hindsight_integration  # noqa: E402

logger = logging.getLogger("competeiq.startup")

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or DEFAULT_CORS_ORIGINS


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Initialize the real Hindsight Cloud client and verify connectivity.
    try:
        available = await hindsight_integration.initialize()
        logger.info(
            "Hindsight startup initialization: %s",
            "connected" if available else "unavailable",
        )
    except Exception:  # noqa: BLE001
        logger.exception("Hindsight startup initialization failed")

    # Authenticate each configured Band agent without blocking the event loop.
    try:
        available = await asyncio.to_thread(band_integration.initialize)
        logger.info(
            "BAND AI startup initialization: %s",
            "connected" if available else "no agent authenticated",
        )
    except Exception:  # noqa: BLE001
        logger.exception("BAND AI startup initialization failed")

    try:
        yield
    finally:
        try:
            await hindsight_integration.aclose()
        except Exception:  # noqa: BLE001
            logger.exception("Hindsight shutdown failed")


app = FastAPI(
    title="CompeteIQ API",
    description="NEXORA AI - Competitive Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all CompeteIQ API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "CompeteIQ API is running",
        "company": "NEXORA AI",
        "status": "online",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
