from collections.abc import Sequence

from sqlalchemy import or_, select

from app.classrooms.models.classrooms_db import (
    Classroom,
    ClassroomSearchRequestSchema,
    IndividualClassroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.common.sqlalchemy_ext import db


async def retrieve_paginated_classrooms_by_student_id(
    student_id: int,
    search_params: ClassroomSearchRequestSchema,
) -> Sequence[Classroom]:
    stmt = Classroom.select_by_search_params(
        stmt=select(Classroom)
        .join(Enrollment, isouter=True)
        .filter(
            or_(
                Enrollment.student_id == student_id,
                IndividualClassroom.student_id == student_id,
            )
        ),
        search_params=search_params,
    )
    return await db.get_all(stmt=stmt)


async def retrieve_paginated_classrooms_by_tutor_id(
    tutor_id: int,
    search_params: ClassroomSearchRequestSchema,
) -> Sequence[Classroom]:
    stmt = Classroom.select_by_search_params(
        stmt=select(Classroom).filter_by(tutor_id=tutor_id),
        search_params=search_params,
    )
    return await db.get_all(stmt=stmt)
