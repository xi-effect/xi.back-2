from typing import Any, Generic, TypeVar

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from tests.common.types import AnyJSON

T = TypeVar("T", bound=BaseModel)


class BaseModelFactory(ModelFactory[T], Generic[T]):
    __is_base_factory__ = True
    __use_defaults__ = True

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(mode="json")


class BasePatchModelFactory(BaseModelFactory[T], Generic[T]):
    __is_base_factory__ = True

    @classmethod
    def build_json(cls, **kwargs: Any) -> AnyJSON:
        return cls.build(**kwargs).model_dump(mode="json", exclude_defaults=True)
