from datetime import datetime
from typing import Any, ClassVar, Self

from sqlalchemy import Dialect, TypeDecorator
from sqlalchemy.dialects.postgresql import BIT

from app.common.utils.bitwise import (
    bitwise_cyclic_shift_left,
    bitwise_cyclic_shift_right,
)


class TimestampRelativeBitmask:
    size: ClassVar[int]

    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def position_from_timestamp(cls, timestamp: datetime) -> int:
        raise NotImplementedError

    def check_if_timestamp_matches(self, timestamp: datetime) -> bool:
        return bool(self.value & (1 << self.position_from_timestamp(timestamp)))

    def replace_origin(self, old_origin: datetime, new_origin: datetime) -> Self:
        position_difference: int = (
            self.position_from_timestamp(new_origin)
            - self.position_from_timestamp(old_origin)
        ) % self.size
        if position_difference > self.size // 2:
            position_difference -= self.size

        if position_difference < 0:
            new_value = bitwise_cyclic_shift_right(
                value=self.value,
                size=self.size,
                rotations=-position_difference,
            )
        elif position_difference > 0:
            new_value = bitwise_cyclic_shift_left(
                value=self.value,
                size=self.size,
                rotations=position_difference,
            )
        else:
            new_value = self.value

        return type(self)(value=new_value)


class WeeklyBitmask(TimestampRelativeBitmask):
    size = 7

    @classmethod
    def position_from_timestamp(cls, timestamp: datetime) -> int:
        return timestamp.weekday()


class PSQLBitmask(TypeDecorator[int]):
    impl = BIT
    cache_ok = True

    @property
    def python_type(self) -> type[Any]:
        return int

    def process_bind_param(self, value: int | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return bin(value).partition("b")[2].rjust(7, "0")

    def process_result_value(self, value: str | None, dialect: Dialect) -> int | None:
        if value is None:
            return None
        return int(value, base=2)
