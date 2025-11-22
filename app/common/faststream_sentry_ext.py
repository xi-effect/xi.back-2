# flake8: noqa FNE005 WPS116 WPS120 WPS436 WPS609

from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Any, ClassVar, Final

import sentry_sdk
from faststream import BaseMiddleware, PublishCommand, StreamMessage
from faststream._internal.fastapi import StreamRouter
from sentry_sdk._types import AnnotatedValue
from sentry_sdk.consts import SPANSTATUS
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations._wsgi_common import request_body_within_bounds
from sentry_sdk.tracing import (
    BAGGAGE_HEADER_NAME,
    SENTRY_TRACE_HEADER_NAME,
    TransactionSource,
)
from sentry_sdk.types import Event, Hint
from sentry_sdk.utils import capture_internal_exceptions

# Inspired by & adapted from the dramatiq sentry integration
INTEGRATION_IDENTIFIER: Final[str] = "faststream"


def apply_size_bounds(data: Any, content_length: int) -> Any:
    return (
        data
        if request_body_within_bounds(sentry_sdk.get_client(), content_length)
        else AnnotatedValue.removed_because_over_size_limit()
    )


class FastStreamSentryMiddleware[PublishCommandType: PublishCommand, RawMessageType](
    BaseMiddleware[PublishCommandType, RawMessageType]
):
    baggage_header_name: ClassVar[str] = "sentry_baggage"
    trace_id_header_name: ClassVar[str] = "sentry_trace_id"

    origin: ClassVar[str] = f"auto.queue.{INTEGRATION_IDENTIFIER}"
    send_message_op_name: ClassVar[str] = f"send.message.{INTEGRATION_IDENTIFIER}"
    process_message_op_name: ClassVar[str] = f"process.message.{INTEGRATION_IDENTIFIER}"

    span_data_correlation_id: ClassVar[str] = "messaging.correlation_id"
    span_data_reply_to: ClassVar[str] = "messaging.reply_to"
    span_data_headers: ClassVar[str] = "messaging.headers"
    span_data_body: ClassVar[str] = "messaging.body"

    def is_integration_disabled(self) -> bool:
        integration = sentry_sdk.get_client().get_integration(FaststreamIntegration)
        return integration is None

    @property
    def raw_message(self) -> dict[str, Any]:
        return self.msg if isinstance(self.msg, dict) else {}

    def event_processor(self, event: Event, _hint: Hint) -> Event | None:
        contexts = event.setdefault("contexts", {})
        faststream_event_context = contexts.setdefault(INTEGRATION_IDENTIFIER, {})
        faststream_event_context["type"] = INTEGRATION_IDENTIFIER

        message = self.context.get_local("message")

        if isinstance(message, StreamMessage):
            faststream_event_context.update(
                {
                    "message_id": message.message_id,
                    "source_type": message.source_type,
                    "reply_to": message.reply_to,
                    "headers": message.headers,
                    "body": apply_size_bounds(message.body, len(message.body)),
                    "committed": message.committed,
                    "processed": message.processed,
                }
            )
        else:
            faststream_event_context["raw_message"] = self.msg

        return event

    async def publish_scope(
        self,
        call_next: Callable[[PublishCommandType], Awaitable[Any]],
        cmd: PublishCommandType,
    ) -> Any:
        if self.is_integration_disabled():
            return await call_next(cmd)

        cmd.add_headers(
            {
                self.baggage_header_name: sentry_sdk.get_baggage(),
                self.trace_id_header_name: sentry_sdk.get_traceparent(),
            }
        )

        with sentry_sdk.start_span(
            op=self.send_message_op_name,
            name=f"{cmd.publish_type.value}: {cmd.destination}",
            origin=self.origin,
        ) as span:
            span_data = {
                self.span_data_correlation_id: cmd.correlation_id,
                self.span_data_reply_to: cmd.reply_to,
                self.span_data_headers: cmd.headers,
                self.span_data_body: cmd.body,
            }
            span_data = {key: value for key, value in span_data.items() if value}

            span.update_data(span_data)

            with capture_internal_exceptions():
                sentry_sdk.add_breadcrumb(
                    category=self.send_message_op_name,
                    message=f"{cmd.publish_type} {cmd.destination}",
                    data=span_data,
                )

            return await call_next(cmd)

    async def on_receive(self) -> None:
        if self.is_integration_disabled():
            return await super().on_receive()

        scope_manager = sentry_sdk.isolation_scope()
        self.context.set_local("sentry_scope_manager", scope_manager)

        scope = scope_manager.__enter__()
        scope.clear_breadcrumbs()
        scope.add_event_processor(self.event_processor)

        message_ids = self.raw_message.get("message_ids")
        if message_ids is not None:
            scope.set_extra("faststream_message_ids", message_ids)

        return await super().on_receive()

    async def consume_scope(
        self,
        call_next: Callable[[StreamMessage[RawMessageType]], Awaitable[Any]],
        msg: StreamMessage[RawMessageType],
    ) -> Any:
        if self.is_integration_disabled():
            return await call_next(msg)

        transaction = sentry_sdk.continue_trace(
            {
                BAGGAGE_HEADER_NAME: msg.headers.get(self.baggage_header_name),
                SENTRY_TRACE_HEADER_NAME: msg.headers.get(self.trace_id_header_name),
            },
            name=self.raw_message.get("channel", INTEGRATION_IDENTIFIER),
            op=self.process_message_op_name,
            source=TransactionSource.TASK,
            origin=self.origin,
        )
        transaction.set_status(SPANSTATUS.OK)
        with sentry_sdk.start_transaction(transaction):
            return await call_next(msg)

    async def after_processed(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> bool | None:
        if self.is_integration_disabled():
            return await super().after_processed(exc_type, exc_val, exc_tb)

        scope_manager = self.context.get_local("sentry_scope_manager")

        if exc_val is None:
            scope_manager.__exit__(None, None, None)
        else:
            sentry_sdk.capture_exception(exc_val)
            scope_manager.__exit__(exc_type, exc_val, exc_tb)

        return await super().after_processed(exc_type, exc_val, exc_tb)


def patch_faststream_stream_router() -> None:
    original_stream_router__init__ = StreamRouter.__init__

    def sentry_stream_router__init__(
        self: StreamRouter[Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        middlewares = kwargs.get("middlewares")
        if middlewares is None:
            middlewares = []
        else:
            middlewares = list(middlewares)

        middlewares.insert(0, FastStreamSentryMiddleware)
        kwargs["middlewares"] = middlewares

        original_stream_router__init__(self, *args, **kwargs)

    StreamRouter.__init__ = sentry_stream_router__init__  # type: ignore[method-assign]


class FaststreamIntegration(Integration):
    identifier = INTEGRATION_IDENTIFIER

    @staticmethod
    def setup_once() -> None:
        patch_faststream_stream_router()
