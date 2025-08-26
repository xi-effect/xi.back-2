from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.tutors.models.classrooms_db import (
    Classroom,
    GroupClassroom,
    IndividualClassroom,
)


class ClassroomResponses(Responses):
    CLASSROOM_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Classroom not found"


@with_responses(ClassroomResponses)
async def get_classroom_by_id(classroom_id: Annotated[int, Path()]) -> Classroom:
    classroom = await Classroom.find_first_by_id(classroom_id)
    if classroom is None:
        raise ClassroomResponses.CLASSROOM_NOT_FOUND
    return classroom


ClassroomByID = Annotated[Classroom, Depends(get_classroom_by_id)]


@with_responses(ClassroomResponses)
async def get_individual_classroom_by_id(
    classroom_id: Annotated[int, Path()],
) -> IndividualClassroom:
    individual_classroom = await IndividualClassroom.find_first_by_id(classroom_id)
    if individual_classroom is None:
        raise ClassroomResponses.CLASSROOM_NOT_FOUND
    return individual_classroom


IndividualClassroomByID = Annotated[
    IndividualClassroom, Depends(get_individual_classroom_by_id)
]


@with_responses(ClassroomResponses)
async def get_group_classroom_by_id(
    classroom_id: Annotated[int, Path()],
) -> GroupClassroom:
    group_classroom = await GroupClassroom.find_first_by_id(classroom_id)
    if group_classroom is None:
        raise ClassroomResponses.CLASSROOM_NOT_FOUND
    return group_classroom


GroupClassroomByID = Annotated[GroupClassroom, Depends(get_group_classroom_by_id)]
