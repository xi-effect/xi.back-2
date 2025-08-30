from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.tutors.dependencies.classrooms_dep import (
    ClassroomByID,
    GroupClassroomByID,
    IndividualClassroomByID,
)
from app.tutors.models.classrooms_db import (
    AnyClassroom,
    Classroom,
    GroupClassroom,
    IndividualClassroom,
)


class MyTutorClassroomResponses(Responses):
    TUTOR_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Classroom tutor access denied"


def verify_tutor_classroom_access[T: Classroom](
    auth_data: AuthorizationData, classroom: T
) -> T:
    if classroom.tutor_id != auth_data.user_id:
        raise MyTutorClassroomResponses.TUTOR_ACCESS_DENIED
    return classroom


@with_responses(MyTutorClassroomResponses)
async def get_my_tutor_classroom_by_id(
    auth_data: AuthorizationData, classroom: ClassroomByID
) -> AnyClassroom:
    return verify_tutor_classroom_access(auth_data, classroom)


MyTutorClassroomByID = Annotated[AnyClassroom, Depends(get_my_tutor_classroom_by_id)]


@with_responses(MyTutorClassroomResponses)
async def get_my_tutor_individual_classroom_by_id(
    auth_data: AuthorizationData, individual_classroom: IndividualClassroomByID
) -> IndividualClassroom:
    return verify_tutor_classroom_access(auth_data, individual_classroom)


MyTutorIndividualClassroomByID = Annotated[
    IndividualClassroom, Depends(get_my_tutor_individual_classroom_by_id)
]


@with_responses(MyTutorClassroomResponses)
async def get_my_tutor_group_classroom_by_id(
    auth_data: AuthorizationData, group_classroom: GroupClassroomByID
) -> GroupClassroom:
    return verify_tutor_classroom_access(auth_data, group_classroom)


MyTutorGroupClassroomByID = Annotated[
    GroupClassroom, Depends(get_my_tutor_group_classroom_by_id)
]
