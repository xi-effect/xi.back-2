from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Generator
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)
from typing import Any, Protocol, Self, cast


class TransformerProtocol[InputType, OutputType](Protocol):
    async def __call__(self, data: InputType) -> OutputType:
        pass


class Transformer[InputType, OutputType](ABC):
    @abstractmethod
    async def transform(self, data: InputType) -> OutputType:
        raise NotImplementedError

    async def __call__(self, data: InputType) -> OutputType:
        return await self.transform(data)


class Validator[InputType](Transformer[InputType, InputType]):
    @abstractmethod
    async def validate(self, data: InputType) -> None:
        raise NotImplementedError

    async def transform(self, data: InputType) -> InputType:
        await self.validate(data=data)
        return data


class AsyncRunnerTransformer[OutputType](
    Transformer[Awaitable[OutputType], OutputType]
):
    async def transform(self, data: Awaitable[OutputType]) -> OutputType:
        return await data


class AbstractPipeline[OutputType](ABC):
    def __init__(self, exit_stack: AsyncExitStack | None = None) -> None:
        self.exit_stack: AsyncExitStack = exit_stack or AsyncExitStack()

    @abstractmethod
    async def run(self) -> OutputType:
        raise NotImplementedError

    async def run_wrapped(self) -> OutputType:  # type: ignore[return]  # false-positive
        async with self.exit_stack:
            return await self.run()

    def __await__(self) -> Generator[Any, None, OutputType]:
        return self.run_wrapped().__await__()


class DataPipeline[OutputType](AbstractPipeline[OutputType]):
    def __init__(self, data: OutputType) -> None:
        super().__init__()
        self.data = data

    async def run(self) -> OutputType:
        return self.data


class PipelineWithContext[OutputType](AbstractPipeline[OutputType]):
    def __init__(
        self,
        pipeline: AbstractPipeline[OutputType],
        context_manager: AbstractContextManager[Any],
    ) -> None:
        super().__init__(exit_stack=pipeline.exit_stack)
        self.pipeline = pipeline
        self.context_manager = context_manager

    async def run(self) -> OutputType:
        # TODO pass the manager to pipeline somehow
        result = await self.pipeline.run()
        self.exit_stack.enter_context(self.context_manager)
        return result


class PipelineWithAsyncContext[OutputType](AbstractPipeline[OutputType]):
    def __init__(
        self,
        pipeline: AbstractPipeline[OutputType],
        context_manager: AbstractAsyncContextManager[Any],
    ) -> None:
        super().__init__(exit_stack=pipeline.exit_stack)
        self.pipeline = pipeline
        self.context_manager = context_manager

    async def run(self) -> OutputType:
        # TODO pass the manager to pipeline somehow
        result = await self.pipeline.run()
        await self.exit_stack.enter_async_context(self.context_manager)
        return result


class TransformedPipeline[InputType, OutputType](AbstractPipeline[OutputType]):
    def __init__(
        self,
        pipeline: AbstractPipeline[InputType],
        transformer: TransformerProtocol[InputType, OutputType],
    ) -> None:
        super().__init__(exit_stack=pipeline.exit_stack)
        self.pipeline = pipeline
        self.transformer = transformer

    async def run(self) -> OutputType:
        return await self.transformer(await self.pipeline.run())


class PipelineBuilder[OutputType]:
    def __init__(self, pipeline: AbstractPipeline[OutputType]) -> None:
        self.pipeline = pipeline

    @classmethod
    def initialize(cls, data: OutputType) -> Self:
        return cls(DataPipeline(data))

    def __await__(self) -> Generator[Any, None, OutputType]:
        return self.pipeline.__await__()

    def enter_context(
        self,
        context_manager: AbstractContextManager[Any],
    ) -> Self:
        return type(self)(PipelineWithContext(self.pipeline, context_manager))

    def enter_async_context(
        self,
        context_manager: AbstractAsyncContextManager[Any],
    ) -> Self:
        return type(self)(PipelineWithAsyncContext(self.pipeline, context_manager))

    def validate(
        self,
        validator: TransformerProtocol[OutputType, OutputType],
    ) -> Self:
        return type(self)(TransformedPipeline(self.pipeline, validator))

    def transform[NewOutputType](
        self,
        transformer: TransformerProtocol[OutputType, NewOutputType],
    ) -> PipelineBuilder[NewOutputType]:
        builder_type = cast(type[PipelineBuilder[Any]], type(self))  # mypy magic
        return builder_type(TransformedPipeline(self.pipeline, transformer))

    # TODO: Whenever python adds support for higher-kinded types, use those here:
    #   `[BuilderType: PipelineBuilder]` & `cls: type[BuilderType[OutputType]`
    #   It kinda works with `[BuilderType: PipelineBuilder[OutputType]`,
    #   but mypy when throws `[type-var]` exceptions for most subclasses
    def swap_builder_type[BuilderType: PipelineBuilder[Any]](
        self, builder_type: type[BuilderType]
    ) -> BuilderType:
        return builder_type(self.pipeline)

    def await_coroutine[NewOutputType](
        self: PipelineBuilder[Awaitable[NewOutputType]],
    ) -> PipelineBuilder[NewOutputType]:
        return self.transform(AsyncRunnerTransformer())
