from collections.abc import Sequence

from sqlalchemy import or_, select

from app.classrooms.models.classrooms_db import (
    Classroom,
    IndividualClassroom,
    RecipientClassroomCursorSchema,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.common.sqlalchemy_ext import db


async def find_classrooms_paginate_by_student_id(
    student_id: int, cursor: RecipientClassroomCursorSchema | None, limit: int
) -> Sequence[Classroom]:
    stmt = (
        select(Classroom)
        .join(Enrollment, isouter=True)
        .filter(
            or_(
                Enrollment.student_id == student_id,
                IndividualClassroom.student_id == student_id,
            )
        )
    )
    if cursor is not None:
        stmt = Classroom.select_after_cursor(stmt=stmt, cursor=cursor)
    return await db.get_all(
        stmt=stmt.order_by(Classroom.created_at.desc()).limit(limit=limit)
    )


async def find_classrooms_paginate_by_tutor_id(
    tutor_id: int, cursor: RecipientClassroomCursorSchema | None, limit: int
) -> Sequence[Classroom]:
    stmt = select(Classroom).filter_by(tutor_id=tutor_id)
    if cursor is not None:
        stmt = Classroom.select_after_cursor(stmt=stmt, cursor=cursor)
    return await db.get_all(
        stmt=stmt.order_by(Classroom.created_at.desc()).limit(limit=limit)
    )
