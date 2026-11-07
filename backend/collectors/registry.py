"""Collector registry — maps source names to collector classes."""

from .base import BaseCollector

_collectors: dict = {}


def register(collector: BaseCollector):
    _collectors[collector.source_name] = collector


def get_collector(source_name: str) -> BaseCollector | None:
    return _collectors.get(source_name)


def list_collectors() -> list:
    return list(_collectors.keys())


def collector_registry():
    """Return the registry dict (name -> collector)."""
    return _collectors
