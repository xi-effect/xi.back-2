from typing import Any

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from tests.common.types import AnyJSON


class BaseModelFactory[T: BaseModel](ModelFactory[T]):
    __is_base_factory__ = True
    __use_defaults__ = True

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(mode="json")


class BasePatchModelFactory[T: BaseModel](BaseModelFactory[T]):
    __is_base_factory__ = True

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(mode="json", exclude_defaults=True)
