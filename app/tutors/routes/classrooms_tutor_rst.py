from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.tutors.dependencies.classrooms_tutor_dep import (
    MyTutorClassroomByID,
    MyTutorGroupClassroomByID,
    MyTutorIndividualClassroomByID,
)
from app.tutors.models.classrooms_db import (
    Classroom,
    GroupClassroom,
    IndividualClassroom,
    TutorClassroomResponseSchema,
    UserClassroomStatus,
)

router = APIRouterExt(tags=["tutor classrooms"])


@router.post(
    path="/roles/tutor/group-classrooms/",
    status_code=status.HTTP_201_CREATED,
    response_model=GroupClassroom.TutorResponseSchema,
    summary="Create a new tutor group classroom for the current user",
)
async def create_group_classroom(
    auth_data: AuthorizationData,
    data: GroupClassroom.InputSchema,
) -> GroupClassroom:
    # TODO amount limiting logic (subscription-based)
    return await GroupClassroom.create(
        tutor_id=auth_data.user_id,
        **data.model_dump(),
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/",
    response_model=TutorClassroomResponseSchema,
    summary="Retrieve tutor's classroom by id",
)
async def retrieve_classroom(classroom: MyTutorClassroomByID) -> Classroom:
    return classroom


@router.patch(
    path="/roles/tutor/individual-classrooms/{classroom_id}/",
    response_model=IndividualClassroom.TutorResponseSchema,
    summary="Update tutor's individual classroom by id",
)
async def patch_individual_classroom(
    individual_classroom: MyTutorIndividualClassroomByID,
    data: IndividualClassroom.PatchSchema,
) -> IndividualClassroom:
    individual_classroom.update(**data.model_dump(exclude_defaults=True))
    return individual_classroom


@router.patch(
    path="/roles/tutor/group-classrooms/{classroom_id}/",
    response_model=GroupClassroom.TutorResponseSchema,
    summary="Update tutor's group classroom by id",
)
async def patch_group_classroom(
    group_classroom: MyTutorGroupClassroomByID,
    data: GroupClassroom.PatchSchema,
) -> GroupClassroom:
    group_classroom.update(**data.model_dump(exclude_defaults=True))
    return group_classroom


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/status/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update tutor's classroom's status by id",
)
async def update_classroom_status(
    classroom: MyTutorClassroomByID,
    new_status: Annotated[UserClassroomStatus, Body(alias="status", embed=True)],
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
