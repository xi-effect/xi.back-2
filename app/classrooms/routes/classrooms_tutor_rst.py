from collections.abc import Sequence
from typing import Annotated

from fastapi import Body
from pydantic import AwareDatetime, Field
from sqlalchemy import select
from starlette import status

from app.classrooms.dependencies.classrooms_tutor_dep import (
    MyTutorClassroomByID,
    MyTutorGroupClassroomByID,
    MyTutorIndividualClassroomByID,
)
from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    Classroom,
    GroupClassroom,
    IndividualClassroom,
    TutorClassroomResponseSchema,
    TutorClassroomSearchRequestSchema,
    UserClassroomStatus,
)
from app.classrooms.services import classrooms_svc
from app.common.config_bdg import autocomplete_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.sqlalchemy_ext import db

router = APIRouterExt(tags=["tutor classrooms"])


@router.get(
    path="/roles/tutor/classrooms/",
    response_model=list[TutorClassroomResponseSchema],
    summary="List paginated tutor classrooms for the current user",
    deprecated=True,
)
async def list_classrooms(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[Classroom]:
    stmt = select(Classroom).filter_by(tutor_id=auth_data.user_id)
    if created_before is not None:
        stmt = stmt.filter(Classroom.created_at < created_before)
    return await db.get_all(stmt.order_by(Classroom.created_at.desc()).limit(limit))


@router.post(
    path="/roles/tutor/classrooms/searches/",
    response_model=list[TutorClassroomResponseSchema],
    summary="List with filters and paginated tutor classrooms for the current user",
)
async def list_classrooms_by_filter(
    auth_data: AuthorizationData, data: TutorClassroomSearchRequestSchema
) -> Sequence[Classroom]:
    return await classrooms_svc.find_classrooms_paginate_by_tutor_id(
        tutor_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


class SubjectResponses(Responses):
    SUBJECT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Subject not found"


async def validate_subject(
    new_subject_id: int | None,
    old_subject_id: int | None = None,
) -> None:
    if new_subject_id is None:
        return

    if new_subject_id == old_subject_id:
        return

    subject = await autocomplete_bridge.retrieve_subject(subject_id=new_subject_id)
    if subject is None:
        raise SubjectResponses.SUBJECT_NOT_FOUND


@router.post(
    path="/roles/tutor/group-classrooms/",
    status_code=status.HTTP_201_CREATED,
    response_model=GroupClassroom.TutorResponseSchema,
    responses=SubjectResponses.responses(),
    summary="Create a new tutor group classroom for the current user",
)
async def create_group_classroom(
    auth_data: AuthorizationData,
    data: GroupClassroom.InputSchema,
) -> GroupClassroom:
    # TODO amount limiting logic (subscription-based)
    await validate_subject(new_subject_id=data.subject_id)
    return await GroupClassroom.create(
        tutor_id=auth_data.user_id,
        **data.model_dump(),
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/",
    response_model=TutorClassroomResponseSchema,
    summary="Retrieve tutor's classroom by id",
)
async def retrieve_classroom(classroom: MyTutorClassroomByID) -> AnyClassroom:
    return classroom


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/access/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Verify access to tutor's classroom by id",
)
async def verify_classroom_access(_classroom: MyTutorClassroomByID) -> None:
    pass


@router.patch(
    path="/roles/tutor/individual-classrooms/{classroom_id}/",
    response_model=IndividualClassroom.TutorResponseSchema,
    responses=SubjectResponses.responses(),
    summary="Update tutor's individual classroom by id",
)
async def patch_individual_classroom(
    individual_classroom: MyTutorIndividualClassroomByID,
    data: IndividualClassroom.PatchSchema,
) -> IndividualClassroom:
    data_to_update = data.model_dump(exclude_defaults=True)
    await validate_subject(
        new_subject_id=data_to_update.get("subject_id"),
        old_subject_id=individual_classroom.subject_id,
    )
    individual_classroom.update(**data_to_update)
    return individual_classroom


@router.patch(
    path="/roles/tutor/group-classrooms/{classroom_id}/",
    response_model=GroupClassroom.TutorResponseSchema,
    responses=SubjectResponses.responses(),
    summary="Update tutor's group classroom by id",
)
async def patch_group_classroom(
    group_classroom: MyTutorGroupClassroomByID,
    data: GroupClassroom.PatchSchema,
) -> GroupClassroom:
    data_to_update = data.model_dump(exclude_defaults=True)
    await validate_subject(
        new_subject_id=data_to_update.get("subject_id"),
        old_subject_id=group_classroom.subject_id,
    )
    group_classroom.update(**data_to_update)
    return group_classroom


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/status/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update tutor's classroom's status by id",
)
async def update_classroom_status(
    classroom: MyTutorClassroomByID,
    new_status: Annotated[
        UserClassroomStatus,
        Body(alias="status", validation_alias="status", embed=True),
    ],
) -> None:
    # TODO state-transition logic (subscription-based)
    classroom.status = new_status


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tutor's classroom by id",
)
async def delete_classroom(classroom: MyTutorClassroomByID) -> None:
    await classroom.delete()
