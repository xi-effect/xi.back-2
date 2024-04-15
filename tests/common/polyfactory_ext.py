from typing import Generic, TypeVar

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseModelFactory(ModelFactory[T], Generic[T]):
    __is_base_factory__ = True
    __use_defaults__ = True
