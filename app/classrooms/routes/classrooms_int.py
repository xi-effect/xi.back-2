from collections.abc import Sequence
from typing import assert_never

from app.classrooms.dependencies.classrooms_dep import ClassroomByID
from app.classrooms.models.classrooms_db import GroupClassroom, IndividualClassroom
from app.classrooms.models.enrollments_db import Enrollment
from app.common.fastapi_ext import APIRouterExt

router = APIRouterExt(tags=["classrooms internal"])


@router.get(
    path="/classrooms/{classroom_id}/students/",
    summary="List all student ids in a classroom by id",
)
async def list_classroom_student_ids(classroom: ClassroomByID) -> Sequence[int]:
    match classroom:
        case IndividualClassroom():
            return [classroom.student_id]
        case GroupClassroom():
            return await Enrollment.find_all_student_ids_by_classroom_id(
                group_classroom_id=classroom.id
            )
        case _:
            assert_never(classroom)
