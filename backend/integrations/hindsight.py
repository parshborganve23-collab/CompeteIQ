"""Hindsight Memory integration — real SDK integration.

Uses the official hindsight_client Python SDK (1.2.0) against Hindsight Cloud
or a self-hosted Hindsight API server. The client is initialized during
FastAPI startup and can also be initialized lazily on demand. It never
simulates a successful Hindsight response.

Official docs: https://docs.hindsight.vectorize.io/cloud/python-sdk/
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from hindsight_client import Hindsight

logger = logging.getLogger(__name__)

# Load backend/.env regardless of the process working directory. Existing
# environment variables take precedence (load_dotenv defaults to no override).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class HindsightStatus:
    configured: bool
    available: bool
    reason: str
    banks: List[str] = field(default_factory=list)
    setup_instructions: List[str] = field(default_factory=list)
    version: Optional[str] = None


class HindsightIntegration:
    """Wrapper around the official hindsight_client Python SDK.

    Initialization is idempotent and protected by an asyncio lock. A failed
    attempt is retried after a short cooldown so a transient network error at
    startup does not leave the integration permanently unavailable.
    """

    # Dedicated CompeteIQ memory bank
    BANK_COMPETEIQ = "competeiq-intelligence"

    # Seconds to wait between failed initialization attempts
    RETRY_COOLDOWN_SECONDS = 20.0

    def __init__(self):
        self.api_url: Optional[str] = os.getenv("HINDSIGHT_API_URL")
        self.api_key: Optional[str] = os.getenv("HINDSIGHT_API_KEY")
        self.timeout: float = float(os.getenv("HINDSIGHT_TIMEOUT_SECONDS", "20"))
        self._client: Optional[Hindsight] = None
        self._initialized: bool = False
        self._available: bool = False
        self._init_error: Optional[str] = None
        self._version: Optional[str] = None
        self._last_attempt: float = 0.0
        self._lock: Optional[asyncio.Lock] = None
        self._setup_instructions: List[str] = []

        if not self.api_url:
            self._setup_instructions = [
                "Hindsight is not configured.",
                "1. Set HINDSIGHT_API_URL=https://api.hindsight.vectorize.io in backend/.env",
                "2. Set HINDSIGHT_API_KEY to your Hindsight Cloud API key",
                "3. Restart the CompeteIQ backend.",
            ]

    # ---------- helpers ----------

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _sanitize(self, value: Any) -> str:
        """Remove credentials from error messages before exposing them."""
        text = str(value)
        if self.api_key:
            text = text.replace(self.api_key, "***")
        return text

    def _setup_instructions_for_error(self, exc: Exception) -> List[str]:
        return [
            f"Hindsight client initialization failed: {self._sanitize(exc)}",
            "Verify HINDSIGHT_API_URL and HINDSIGHT_API_KEY in backend/.env.",
            "Confirm the key is valid at https://docs.hindsight.vectorize.io/cloud/python-sdk/",
            "Then restart the CompeteIQ backend.",
        ]

    def _require_available(self):
        if not self._available or self._client is None:
            raise RuntimeError(
                "Hindsight is not available. "
                f"{self._init_error or 'Client has not been initialized.'}"
            )

    # ---------- initialization ----------

    async def initialize(self, force: bool = False) -> bool:
        """Initialize the client and verify the real API connection."""
        await self._ensure_client(force=force)
        return self._available

    async def _ensure_client(self, force: bool = False):
        """Lazily initialize the Hindsight client within an async context."""
        if self._available and not force:
            return

        if not self.api_url:
            self._initialized = True
            self._available = False
            self._init_error = "HINDSIGHT_API_URL not set"
            return

        # Avoid hammering the API after a recent failure.
        if (
            not force
            and self._init_error
            and self._last_attempt
            and (time.monotonic() - self._last_attempt) < self.RETRY_COOLDOWN_SECONDS
        ):
            return

        async with self._get_lock():
            if self._available and not force:
                return
            if (
                not force
                and self._init_error
                and self._last_attempt
                and (time.monotonic() - self._last_attempt) < self.RETRY_COOLDOWN_SECONDS
            ):
                return

            self._last_attempt = time.monotonic()
            try:
                kwargs: Dict[str, Any] = {
                    "base_url": self.api_url,
                    "timeout": self.timeout,
                }
                if self.api_key:
                    kwargs["api_key"] = self.api_key

                self._client = Hindsight(**kwargs)
                version = await self._client.aget_version()

                self._version = getattr(version, "api_version", None)
                self._available = True
                self._initialized = True
                self._init_error = None
                self._setup_instructions = []
                logger.info(
                    "Hindsight connected: bank=%s api_version=%s",
                    self.BANK_COMPETEIQ,
                    self._version,
                )
            except ImportError:
                self._initialized = True
                self._available = False
                self._init_error = "hindsight-client is not installed"
                self._setup_instructions = [
                    "HINDSIGHT_API_URL is set, but hindsight-client is not installed.",
                    "Run: pip install hindsight-client",
                    "Then restart the CompeteIQ backend.",
                ]
            except Exception as exc:  # noqa: BLE001
                self._initialized = True
                self._available = False
                self._init_error = self._sanitize(exc)
                self._setup_instructions = self._setup_instructions_for_error(exc)
                logger.warning("Hindsight initialization failed: %s", self._init_error)

    # ---------- status ----------

    def is_configured(self) -> bool:
        return bool(self.api_url)

    def is_available(self) -> bool:
        return self._available

    def status(self) -> HindsightStatus:
        if not self.api_url:
            return HindsightStatus(
                configured=False,
                available=False,
                reason="HINDSIGHT_API_URL not set",
                setup_instructions=self._setup_instructions,
            )
        if not self._available:
            reason = self._init_error or "Hindsight client not initialized"
            if not self.api_key:
                reason = f"{reason} (HINDSIGHT_API_KEY is not set)"
            return HindsightStatus(
                configured=True,
                available=False,
                reason=reason,
                setup_instructions=self._setup_instructions,
                version=self._version,
            )
        return HindsightStatus(
            configured=True,
            available=True,
            reason="Connected to Hindsight API",
            banks=[self.BANK_COMPETEIQ],
            version=self._version,
        )

    async def astatus(self) -> HindsightStatus:
        """Ensure initialization has been attempted, then return live status."""
        await self._ensure_client()
        return self.status()

    async def aclose(self) -> None:
        """Close the underlying HTTP client during application shutdown."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:  # noqa: BLE001
                logger.debug("Hindsight client close failed", exc_info=True)
            finally:
                self._client = None
                self._available = False

    # ---------- real Hindsight operations ----------

    def retain(
        self,
        content: str,
        bank_id: str = BANK_COMPETEIQ,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
    ) -> dict:
        """Retain (store) a memory in a Hindsight bank (real API)."""
        self._require_available()
        try:
            result = self._client.retain(
                bank_id=bank_id,
                content=content,
                context=context or "competeiq-intelligence",
                metadata=metadata or {},
                retain_async=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight retain failed: {self._sanitize(exc)}"
            ) from exc
        return {
            "ok": True,
            "bank_id": bank_id,
            "content": content,
            "metadata": metadata or {},
            "operation_id": getattr(result, "operation_id", None),
            "retained_at": _utcnow(),
        }

    async def aretain(
        self,
        content: str,
        bank_id: str = BANK_COMPETEIQ,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
    ) -> dict:
        """Async retain (store) a memory in a Hindsight bank (real API)."""
        await self._ensure_client()
        self._require_available()
        try:
            result = await self._client.aretain(
                bank_id=bank_id,
                content=content,
                context=context or "competeiq-intelligence",
                metadata=metadata or {},
                retain_async=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight aretain failed: {self._sanitize(exc)}"
            ) from exc
        return {
            "ok": True,
            "bank_id": getattr(result, "bank_id", bank_id),
            "content": content,
            "metadata": metadata or {},
            "operation_id": getattr(result, "operation_id", None),
            "items_count": getattr(result, "items_count", None),
            "retained_at": _utcnow(),
        }

    @staticmethod
    def _memory_from_recall(r: Any, bank_id: str) -> dict:
        scores = getattr(r, "scores", None)
        return {
            "id": getattr(r, "id", "") or "",
            "content": getattr(r, "text", "") or "",
            "type": getattr(r, "type", "") or "",
            "bank_id": bank_id,
            "score": getattr(scores, "final", None) if scores is not None else None,
            "timestamp": (
                getattr(r, "mentioned_at", None)
                or getattr(r, "occurred_start", None)
            ),
        }

    def recall(
        self,
        query: str,
        bank_id: str = BANK_COMPETEIQ,
        limit: int = 10,
        budget: str = "mid",
    ) -> List[dict]:
        """Recall relevant memories from a Hindsight bank (real API)."""
        self._require_available()
        try:
            response = self._client.recall(
                bank_id=bank_id,
                query=query,
                max_tokens=4096,
                budget=budget,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight recall failed: {self._sanitize(exc)}"
            ) from exc

        return [
            self._memory_from_recall(r, bank_id)
            for r in (response.results or [])[:limit]
        ]

    async def arecall(
        self,
        query: str,
        bank_id: str = BANK_COMPETEIQ,
        limit: int = 10,
        budget: str = "mid",
    ) -> List[dict]:
        """Async recall relevant memories from a Hindsight bank (real API)."""
        await self._ensure_client()
        self._require_available()
        try:
            response = await self._client.arecall(
                bank_id=bank_id,
                query=query,
                max_tokens=4096,
                budget=budget,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight arecall failed: {self._sanitize(exc)}"
            ) from exc

        return [
            self._memory_from_recall(r, bank_id)
            for r in (response.results or [])[:limit]
        ]

    def reflect(
        self,
        query: str,
        bank_id: str = BANK_COMPETEIQ,
        budget: str = "mid",
        context: Optional[str] = None,
    ) -> dict:
        """Run agentic reasoning over a Hindsight bank (real API)."""
        self._require_available()
        try:
            answer = self._client.reflect(
                bank_id=bank_id,
                query=query,
                budget=budget,
                context=context or "competeiq-strategic-recommendation",
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight reflect failed: {self._sanitize(exc)}"
            ) from exc
        return {
            "ok": True,
            "bank_id": bank_id,
            "reflection": getattr(answer, "text", "") or str(answer),
            "reflected_at": _utcnow(),
        }

    async def areflect(
        self,
        query: str,
        bank_id: str = BANK_COMPETEIQ,
        budget: str = "mid",
        context: Optional[str] = None,
    ) -> dict:
        """Async reflect over a Hindsight bank (real API)."""
        await self._ensure_client()
        self._require_available()
        try:
            answer = await self._client.areflect(
                bank_id=bank_id,
                query=query,
                budget=budget,
                context=context or "competeiq-strategic-recommendation",
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight areflect failed: {self._sanitize(exc)}"
            ) from exc
        return {
            "ok": True,
            "bank_id": bank_id,
            "reflection": getattr(answer, "text", "") or str(answer),
            "structured_output": getattr(answer, "structured_output", None),
            "reflected_at": _utcnow(),
        }

    @staticmethod
    def _memory_from_list_item(m: Any, bank_id: str) -> dict:
        return {
            "id": getattr(m, "id", "") or "",
            "content": getattr(m, "text", "") or "",
            "type": getattr(m, "fact_type", "") or "",
            "bank_id": bank_id,
            "timestamp": (
                getattr(m, "mentioned_at", None)
                or getattr(m, "occurred_start", None)
            ),
            "state": getattr(m, "state", None),
        }

    def list_memories(
        self,
        bank_id: str = BANK_COMPETEIQ,
        search_query: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """List memories in a bank (real API)."""
        self._require_available()
        try:
            response = self._client.list_memories(
                bank_id=bank_id,
                search_query=search_query,
                limit=limit,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight list_memories failed: {self._sanitize(exc)}"
            ) from exc

        items = getattr(response, "items", None)
        if items is None:
            items = response if isinstance(response, list) else []
        return [self._memory_from_list_item(m, bank_id) for m in items]

    async def alist_memories(
        self,
        bank_id: str = BANK_COMPETEIQ,
        search_query: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Async list memories in a bank (real API)."""
        await self._ensure_client()
        self._require_available()
        try:
            response = await self._client.alist_memories(
                bank_id=bank_id,
                search_query=search_query,
                limit=limit,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Hindsight alist_memories failed: {self._sanitize(exc)}"
            ) from exc

        items = getattr(response, "items", None)
        if items is None:
            items = response if isinstance(response, list) else []
        return [self._memory_from_list_item(m, bank_id) for m in items]

    # ---------- CompeteIQ Hindsight workflow ----------

    def run_workflow(self, event: dict) -> dict:
        """Run the full Hindsight workflow for a trending intelligence event."""
        self._require_available()

        title = event.get("title", "")
        company = event.get("company", "")
        description = event.get("description", "")
        category = event.get("category", "")
        event_id = event.get("id", "")

        # 1. Recall relevant historical events
        historical_events = self.recall(
            query=f"{title} {description} {company} {category}",
            bank_id=self.BANK_COMPETEIQ,
            limit=10,
        )

        # Build context from retrieved memories
        context_parts = []
        for m in historical_events:
            context_parts.append(f"- {m['content'][:300]}")
        historical_context = (
            "\n".join(context_parts) if context_parts else "No prior memories found."
        )

        # 2. Reflect to generate a recommendation
        reflection_query = (
            f"Current competitor event: {title} ({company}, {category})\n"
            f"Description: {description}\n\n"
            f"Historical memories from CompeteIQ:\n{historical_context}\n\n"
            "Generate a strategic recommendation for NEXORA AI based on this "
            "competitor event and the historical memories above. Identify "
            "similarities, differences, risks, opportunities, and a recommended "
            "action with priority and confidence."
        )
        reflection = self.reflect(
            query=reflection_query,
            bank_id=self.BANK_COMPETEIQ,
        )

        # 3. Retain the current event as a new historical memory
        self.retain(
            content=(
                f"Competitor event: {title}\n"
                f"Company: {company}\n"
                f"Category: {category}\n"
                f"Description: {description}"
            ),
            bank_id=self.BANK_COMPETEIQ,
            metadata={
                "source": "competeiq-trending-event",
                "company": company,
                "category": category,
                "event_id": event_id,
                "type": "competitor_event",
            },
            context="competeiq-intelligence",
        )

        # 4. Retain the generated recommendation as a strategy memory
        self.retain(
            content=(
                f"Strategic recommendation for event '{title}' ({company}):\n"
                f"{reflection['reflection']}"
            ),
            bank_id=self.BANK_COMPETEIQ,
            metadata={
                "source": "competeiq-strategy",
                "company": company,
                "category": category,
                "event_id": event_id,
                "type": "strategic_recommendation",
            },
            context="competeiq-strategy",
        )

        return {
            "current_event": event,
            "historical_events": historical_events,
            "historical_events_count": len(historical_events),
            "historical_context": historical_context,
            "recommended_action": reflection["reflection"],
            "priority": "medium",
            "confidence": "medium",
            "evidence": [m["content"][:200] for m in historical_events[:3]],
            "expected_impact": "Strategic recommendation based on Hindsight historical memory.",
            "memory_influence": (
                f"Retrieved {len(historical_events)} historical memories from "
                f"Hindsight bank '{self.BANK_COMPETEIQ}'."
            ),
            "retained_event": True,
            "retained_recommendation": True,
            "hindsight_available": True,
        }


# Singleton instance
hindsight_integration = HindsightIntegration()
