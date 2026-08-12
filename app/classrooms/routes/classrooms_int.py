from collections.abc import Sequence
from typing import Annotated, assert_never

from fastapi import Path, Query
from sqlalchemy import or_, select

from app.classrooms.dependencies.classrooms_dep import ClassroomByID
from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    Classroom,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.sqlalchemy_ext import db

router = APIRouterExt(tags=["classrooms internal"])


async def list_classroom_student_ids(classroom: AnyClassroom) -> Sequence[int]:
    match classroom:
        case IndividualClassroom():
            return [classroom.student_id]
        case GroupClassroom():
            return await Enrollment.find_all_student_ids_by_classroom_id(
                group_classroom_id=classroom.id
            )
        case _:
            assert_never(classroom)


@router.get(
    path="/classrooms/{classroom_id}/participant-ids/",
    summary="List participant ids in a classroom by id filtered by role",
)
async def list_classroom_participant_ids(
    classroom: ClassroomByID,
    role: Annotated[ClassroomRole | None, Query()] = None,
) -> Sequence[int]:
    match role:
        case ClassroomRole.TUTOR:
            return [classroom.tutor_id]
        case ClassroomRole.STUDENT:
            return await list_classroom_student_ids(classroom=classroom)
        case None:
            return [
                classroom.tutor_id,
                *await list_classroom_student_ids(classroom=classroom),
            ]
        case _:
            assert_never(role)


@router.get(
    path="/tutors/{tutor_id}/classroom-ids/",
    summary="List all classroom ids for a tutor by id",
)
async def list_tutor_classroom_ids(
    tutor_id: Annotated[int, Path()],
) -> list[int]:
    return await db.get_all_with_assumed_limit(
        select(Classroom.id)
        .filter_by(tutor_id=tutor_id)
        .order_by(Classroom.created_at.desc()),
        limit=100,
    )


@router.get(
    path="/students/{student_id}/classroom-ids/",
    summary="List all classroom ids for a student by id",
)
async def list_student_classroom_ids(
    student_id: Annotated[int, Path()],
) -> list[int]:
    return await db.get_all_with_assumed_limit(
        select(Classroom.id)
        .join(Enrollment, isouter=True)
        .filter(
            or_(
                IndividualClassroom.student_id == student_id,
                Enrollment.student_id == student_id,
            )
        )
        .order_by(Classroom.created_at.desc()),
        limit=100,
    )
