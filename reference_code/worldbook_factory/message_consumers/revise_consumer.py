"""Consumer for worldbook factory revise tasks."""

from __future__ import annotations

from typing import Any, Mapping

from apps.messaging.consumer import ConsumerRegistry, RegisteredConsumer
from apps.messaging.topics import TOPIC_WORLDBOOK_FACTORY_REVISE_REQUEST
from apps.shared_protocol.business_book import BusinessBook
from apps.shared_protocol.enums import Intent, Layer
from apps.shared_protocol.error_envelope import ErrorEnvelope
from apps.shared_protocol.result_envelope import ResultEnvelope
from apps.worldbook_factory.service import revise_worldbook


class WorldbookFactoryReviseConsumer:
    def __init__(
        self,
        *,
        name: str = "worldbook_factory.revise_consumer",
    ) -> None:
        self.name = name

    def handle(self, message: Mapping[str, Any]) -> dict[str, Any]:
        try:
            book_payload = self._extract_book_payload(message)
            book = BusinessBook.from_dict(book_payload)
        except Exception as exc:
            return self._build_malformed_envelope(message=message, exc=exc)

        try:
            if book.intent != Intent.WORLDBOOK_FACTORY_REVISE:
                raise ValueError("worldbook_factory_revise_consumer requires intent=worldbook_factory.revise")
            payload = revise_worldbook(book.payload)
            envelope = ResultEnvelope.from_book(
                book,
                source_layer=Layer.WORLDBOOK_FACTORY,
                target_layer=book.source_layer,
                payload=payload,
                runtime={
                    "consumer": self.name,
                    "operation": "revise",
                    "layer": Layer.WORLDBOOK_FACTORY.value,
                },
            )
            return envelope.to_dict()
        except Exception as exc:
            error = ErrorEnvelope.from_book(
                book,
                source_layer=Layer.WORLDBOOK_FACTORY,
                target_layer=book.source_layer,
                error_code="worldbook_factory.revise_failed",
                error_message=str(exc),
                retriable=False,
                details={"consumer": self.name, "operation": "revise"},
            )
            return error.to_dict()

    @staticmethod
    def _extract_book_payload(message: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(message, Mapping):
            raise ValueError("message must be an object")
        payload = message.get("book")
        if not isinstance(payload, Mapping):
            raise ValueError("message.book is required")
        return payload

    @staticmethod
    def _build_malformed_envelope(
        *,
        message: Mapping[str, Any],
        exc: Exception,
    ) -> dict[str, Any]:
        trace_id = "unknown_trace"
        maybe_trace = message.get("trace_id") if isinstance(message, Mapping) else None
        if isinstance(maybe_trace, str) and maybe_trace:
            trace_id = maybe_trace
        error = ErrorEnvelope(
            trace_id=trace_id,
            book_id="unknown_book",
            parent_book_id=None,
            source_layer=Layer.WORLDBOOK_FACTORY,
            target_layer=Layer.FRONTEND,
            error_code="worldbook_factory.malformed_message",
            error_message=str(exc),
            retriable=False,
            details={"consumer": "worldbook_factory.revise"},
        )
        return error.to_dict()


def register_worldbook_factory_revise_consumer(
    registry: ConsumerRegistry,
    *,
    consumer: WorldbookFactoryReviseConsumer,
    topic: str = TOPIC_WORLDBOOK_FACTORY_REVISE_REQUEST,
) -> RegisteredConsumer:
    return registry.register(topic, consumer.handle, name=consumer.name)
