"""Messaging consumers for worldbook factory."""

from __future__ import annotations

from apps.messaging.consumer import ConsumerRegistry
from apps.worldbook_factory.message_consumers.generate_consumer import (
    WorldbookFactoryGenerateConsumer,
    register_worldbook_factory_generate_consumer,
)
from apps.worldbook_factory.message_consumers.revise_consumer import (
    WorldbookFactoryReviseConsumer,
    register_worldbook_factory_revise_consumer,
)


def register_worldbook_factory_consumers(
    registry: ConsumerRegistry,
) -> dict[str, str]:
    generate_consumer = WorldbookFactoryGenerateConsumer()
    revise_consumer = WorldbookFactoryReviseConsumer()
    generate_registration = register_worldbook_factory_generate_consumer(
        registry,
        consumer=generate_consumer,
    )
    revise_registration = register_worldbook_factory_revise_consumer(
        registry,
        consumer=revise_consumer,
    )
    return {
        generate_registration.topic: generate_registration.name,
        revise_registration.topic: revise_registration.name,
    }


__all__ = [
    "WorldbookFactoryGenerateConsumer",
    "WorldbookFactoryReviseConsumer",
    "register_worldbook_factory_consumers",
    "register_worldbook_factory_generate_consumer",
    "register_worldbook_factory_revise_consumer",
]
