"""Worldbook factory API entry for messaging consumers."""

from __future__ import annotations

from typing import Any

from apps.messaging.consumer import ConsumerRegistry
from apps.worldbook_factory.message_consumers import register_worldbook_factory_consumers


def get_api_info() -> dict[str, Any]:
    return {
        "layer": "worldbook_factory",
        "status": "consumers_ready",
        "phase": "7",
    }


def bootstrap_worldbook_factory_consumers(
    registry: ConsumerRegistry | None = None,
) -> dict[str, Any]:
    target_registry = registry or ConsumerRegistry()
    registered = register_worldbook_factory_consumers(target_registry)
    return {
        "layer": "worldbook_factory",
        "phase": "7",
        "registered_topics": sorted(registered.keys()),
        "consumers": registered,
    }
