from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.tutors.dependencies.classrooms_dep import ClassroomByID
from app.tutors.models.classrooms_db import (
    AnyClassroom,
    GroupClassroom,
    IndividualClassroom,
)
from app.tutors.models.enrollments_db import Enrollment


class MyStudentClassroomResponses(Responses):
    STUDENT_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Classroom student access denied"


async def has_no_student_classroom_access(
    classroom: AnyClassroom,
    student_id: int,
) -> bool:
    match classroom:
        case IndividualClassroom():
            return classroom.student_id != student_id
        case GroupClassroom():
            return (
                await Enrollment.find_first_by_kwargs(
                    group_classroom_id=classroom.id,
                    student_id=student_id,
                )
                is None
            )


@with_responses(MyStudentClassroomResponses)
async def get_my_student_classroom_by_id(
    classroom: ClassroomByID, auth_data: AuthorizationData
) -> AnyClassroom:
    if await has_no_student_classroom_access(
        classroom=classroom, student_id=auth_data.user_id
    ):
        raise MyStudentClassroomResponses.STUDENT_ACCESS_DENIED
    return classroom


MyStudentClassroomByID = Annotated[
    AnyClassroom, Depends(get_my_student_classroom_by_id)
]
