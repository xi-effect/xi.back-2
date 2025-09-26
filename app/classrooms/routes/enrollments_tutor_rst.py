from starlette import status

from app.classrooms.dependencies.classrooms_tutor_dep import (
    MyTutorGroupClassroomByID,
)
from app.classrooms.dependencies.tutorships_dep import MyTutorTutorshipByIDs
from app.classrooms.models.classrooms_db import GroupClassroom
from app.classrooms.models.enrollments_db import Enrollment
from app.common.config_bdg import users_internal_bridge
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.responses import LimitedListResponses
from app.common.schemas.users_sch import UserProfileWithIDSchema

router = APIRouterExt(tags=["classroom enrollments"])


@router.get(
    path="/roles/tutor/group-classrooms/{classroom_id}/students/",
    summary="List all tutor students in a group classroom by ids",
)
async def list_classroom_students(
    group_classroom: MyTutorGroupClassroomByID,
) -> list[UserProfileWithIDSchema]:
    student_ids = await Enrollment.find_all_student_ids_by_classroom_id(
        group_classroom_id=group_classroom.id
    )
    if len(student_ids) == 0:
        return []

    user_id_to_profile = await users_internal_bridge.retrieve_multiple_users(
        user_ids=list(student_ids)
    )
    return [
        UserProfileWithIDSchema(
            **user_id_to_profile[student_id].model_dump(),
            user_id=student_id,
        )
        for student_id in student_ids
    ]


class ExistingEnrollmentResponses(Responses):
    ENROLLMENT_ALREADY_EXISTS = status.HTTP_409_CONFLICT, "Enrollment already exists"


@router.post(
    path="/roles/tutor/group-classrooms/{classroom_id}/students/{student_id}/",
    status_code=status.HTTP_201_CREATED,
    responses=Responses.chain(ExistingEnrollmentResponses, LimitedListResponses),
    summary="Add a tutor student to a group classroom by ids",
)
async def add_classroom_student(
    group_classroom: MyTutorGroupClassroomByID,
    tutorship: MyTutorTutorshipByIDs,
) -> None:
    if (
        await Enrollment.find_first_by_kwargs(
            group_classroom_id=group_classroom.id,
            student_id=tutorship.student_id,
        )
        is not None
    ):
        raise ExistingEnrollmentResponses.ENROLLMENT_ALREADY_EXISTS

    if group_classroom.is_full:
        raise LimitedListResponses.QUANTITY_EXCEEDED

    await GroupClassroom.update_enrollments_count_by_group_classroom_id(
        group_classroom_id=group_classroom.id, delta=1
    )
    await Enrollment.create(
        group_classroom_id=group_classroom.id,
        student_id=tutorship.student_id,
    )


class EnrollmentResponses(Responses):
    ENROLLMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Enrollment not found"


@router.delete(
    path="/roles/tutor/group-classrooms/{classroom_id}/students/{student_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=EnrollmentResponses.responses(),
    summary="Remove a tutor student from a group classroom by ids",
)
async def remove_classroom_student(
    group_classroom: MyTutorGroupClassroomByID,
    student_id: int,
) -> None:
    enrollment = await Enrollment.find_first_by_kwargs(
        group_classroom_id=group_classroom.id,
        student_id=student_id,
    )
    if enrollment is None:
        raise EnrollmentResponses.ENROLLMENT_NOT_FOUND

    await GroupClassroom.update_enrollments_count_by_group_classroom_id(
        group_classroom_id=group_classroom.id, delta=-1
    )
    await enrollment.delete()
