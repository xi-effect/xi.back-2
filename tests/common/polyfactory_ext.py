from collections.abc import Callable
from datetime import timezone
from functools import partial
from typing import Any

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from app.common.pydantic_ext import FutureAwareDatetime, PastAwareDatetime
from tests.common.types import AnyJSON, AnyKwargs


class BaseModelFactory[T: BaseModel](ModelFactory[T]):
    __is_base_factory__ = True

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        mapping = super().get_provider_map().copy()
        mapping[FutureAwareDatetime] = partial(
            cls.__faker__.future_datetime, tzinfo=timezone.utc
        )
        mapping[PastAwareDatetime] = partial(
            cls.__faker__.past_datetime, tzinfo=timezone.utc
        )
        return mapping

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(mode="json", by_alias=True)

    @classmethod
    def build_python(cls, **kwargs: Any) -> AnyKwargs:
        return cls.build(**kwargs).model_dump()


class BasePatchModelFactory[T: BaseModel](BaseModelFactory[T]):
    __is_base_factory__ = True

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(
            mode="json", by_alias=True, exclude_defaults=True
        )

    @classmethod
    def build_python(cls, **kwargs: Any) -> AnyKwargs:
        return cls.build(**kwargs).model_dump(exclude_defaults=True)
