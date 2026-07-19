from collections.abc import Awaitable
from typing import Self

import sentry_sdk
from httpx import Response
from pydantic import TypeAdapter

from app.common.generic_fluid_interface import (
    PipelineBuilder,
    Transformer,
    Validator,
)


class SentryExtraSetter(Validator[Response]):
    async def validate(self, data: Response) -> None:
        sentry_sdk.set_extra("response", data)
        sentry_sdk.set_extra("response_headers", data.headers)
        sentry_sdk.set_extra("response_content", data.content[:1000])


class ResponseStatusValidator(Validator[Response]):
    async def validate(self, data: Response) -> None:
        data.raise_for_status()


class JSONResponseParser[OutputType](Transformer[Response, OutputType]):
    def __init__(self, type_adapter: TypeAdapter[OutputType]) -> None:
        self.type_adapter = type_adapter

    async def transform(self, data: Response) -> OutputType:
        return self.type_adapter.validate_json(data.content)


class ResponsePipelineBuilder(PipelineBuilder[Response]):
    def set_extra_for_sentry(self) -> Self:
        return self.validate(SentryExtraSetter())

    def validate_status_code(self) -> Self:
        return self.validate(ResponseStatusValidator())

    def validate_json[OutputType](
        self, type_adapter: TypeAdapter[OutputType]
    ) -> PipelineBuilder[OutputType]:
        return self.transform(JSONResponseParser(type_adapter))

    @classmethod
    def initialize_from_request(cls, data: Awaitable[Response]) -> Self:
        return (
            PipelineBuilder.initialize(data)
            .enter_context(sentry_sdk.new_scope())
            .await_coroutine()
            .swap_builder_type(cls)
            .set_extra_for_sentry()
        )
