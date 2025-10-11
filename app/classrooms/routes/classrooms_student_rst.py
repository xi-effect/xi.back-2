from collections.abc import Sequence
from typing import Annotated

from pydantic import AwareDatetime, Field
from sqlalchemy import or_, select
from starlette import status

from app.classrooms.dependencies.classrooms_student_dep import MyStudentClassroomByID
from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    Classroom,
    IndividualClassroom,
    StudentClassroomResponseSchema,
    StudentClassroomSearchRequestSchema,
)
from app.classrooms.models.enrollments_db import Enrollment
from app.classrooms.services import classrooms_svc
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.sqlalchemy_ext import db

router = APIRouterExt(tags=["student classrooms"])


@router.get(
    path="/roles/student/classrooms/",
    response_model=list[StudentClassroomResponseSchema],
    summary="List paginated student classrooms for the current user",
    deprecated=True,
)
async def list_classrooms(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Classroom]:
    stmt = (
        select(Classroom)
        .join(Enrollment, isouter=True)
        .filter(
            or_(
                IndividualClassroom.student_id == auth_data.user_id,
                Enrollment.student_id == auth_data.user_id,
            )
        )
    )
    if created_before is not None:
        stmt = stmt.filter(Classroom.created_at < created_before)
    return await db.get_all(stmt.order_by(Classroom.created_at.desc()).limit(limit))


@router.post(
    path="/roles/student/classrooms/searches/",
    response_model=list[StudentClassroomResponseSchema],
    summary="List with filters and paginated student classrooms for the current user",
)
async def list_classrooms_by_filter(
    auth_data: AuthorizationData,
    data: StudentClassroomSearchRequestSchema,
) -> Sequence[Classroom]:
    return await classrooms_svc.find_classrooms_paginate_by_student_id(
        student_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


@router.get(
    path="/roles/student/classrooms/{classroom_id}/",
    response_model=StudentClassroomResponseSchema,
    summary="Retrieve student's classroom by id",
)
async def retrieve_classroom(classroom: MyStudentClassroomByID) -> AnyClassroom:
    return classroom


@router.get(
    path="/roles/student/classrooms/{classroom_id}/access/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verify access to student's classroom by id",
)
async def verify_classroom_access(_classroom: MyStudentClassroomByID) -> None:
    pass
