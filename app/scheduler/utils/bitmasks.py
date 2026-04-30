from datetime import datetime, timedelta
from typing import Any, ClassVar, Self

from sqlalchemy import Dialect, TypeDecorator
from sqlalchemy.dialects.postgresql import BIT

from app.common.utils.bitwise import (
    bitwise_cyclic_shift_left,
    bitwise_cyclic_shift_right,
)


class TimestampRelativeBitmask:
    size: ClassVar[int]
    unit_duration: ClassVar[timedelta]

    @classmethod
    def get_cycle_duration(cls) -> timedelta:
        return cls.size * cls.unit_duration

    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def position_from_timestamp(cls, timestamp: datetime) -> int:
        raise NotImplementedError

    @classmethod
    def build_continuous(
        cls, start_timestamp: datetime, end_timestamp: datetime
    ) -> Self:
        start_position: int = cls.position_from_timestamp(start_timestamp)
        end_position: int = cls.position_from_timestamp(end_timestamp)

        if start_position <= end_position:
            bitmask_value = 0
            for bit_position in range(start_position, end_position + 1):
                bitmask_value ^= 1 << bit_position
        else:
            bitmask_value = (1 << cls.size) - 1
            for bit_position in range(end_position, start_position - 1):
                bitmask_value ^= 1 << bit_position

        return cls(value=bitmask_value)

    def check_if_timestamp_matches(self, timestamp: datetime) -> bool:
        return bool(self.value & (1 << self.position_from_timestamp(timestamp)))

    def calculate_cycle_offset_for_timestamp(self, timestamp: datetime) -> int:
        bitmask_position: int = self.position_from_timestamp(timestamp)
        return (((1 << bitmask_position) - 1) & self.value).bit_count()

    def rotate(self, source_position: int, target_position: int) -> Self:
        position_difference: int = (target_position - source_position) % self.size
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

    def replace_origin(self, old_origin: datetime, new_origin: datetime) -> Self:
        return self.rotate(
            source_position=self.position_from_timestamp(old_origin),
            target_position=self.position_from_timestamp(new_origin),
        )


class WeeklyBitmask(TimestampRelativeBitmask):
    size = 7
    unit_duration = timedelta(days=1)

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
