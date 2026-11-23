from enum import StrEnum, auto

from pydantic import BaseModel

from app.common.schemas.content_sch import FileKind


class PaidPlanKind(StrEnum):
    PRO = auto()


PlanKind = PaidPlanKind | None


class PlanSchema(BaseModel):
    kind: PlanKind
    max_active_classrooms: int
    max_total_storage_bytes: int
    max_file_size_bytes_per_kind: dict[FileKind, int]


class UserPlanUpdateEventSchema(BaseModel):
    user_id: int
