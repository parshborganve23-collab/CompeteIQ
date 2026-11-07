"""CompeteIQ data collectors package.

Collectors poll permitted public data sources (company newsrooms, RSS feeds,
GitHub, Hugging Face, arXiv) and produce IntelligenceEvent records. Collection
is periodic, never real-time. Nothing is fabricated — every event carries a
source URL, collection date, confidence and verification status.
"""

from .base import BaseCollector, CollectorResult
from .registry import collector_registry, get_collector, list_collectors, register

__all__ = [
    "BaseCollector",
    "CollectorResult",
    "collector_registry",
    "get_collector",
    "list_collectors",
]
