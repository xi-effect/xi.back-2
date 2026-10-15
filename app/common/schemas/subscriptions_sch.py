from enum import StrEnum, auto

from pydantic import BaseModel


class PaidPlanKind(StrEnum):
    PRO = auto()


PlanKind = PaidPlanKind | None


class PlanSchema(BaseModel):
    kind: PlanKind
    max_active_classrooms: int
    max_total_storage_bytes: int
