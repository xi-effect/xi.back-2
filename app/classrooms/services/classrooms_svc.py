from starlette import status

from app.classrooms.models.classrooms_db import Classroom, ClassroomStatus
from app.common.config_bdg import subscriptions_bridge
from app.common.fastapi_ext import Responses


async def has_tutor_reached_active_classrooms_limit(tutor_id: int) -> bool:
    plan = await subscriptions_bridge.retrieve_user_plan(user_id=tutor_id)
    active_classrooms_count = await Classroom.count_by_kwargs(
        Classroom.id,
        tutor_id=tutor_id,
        status=ClassroomStatus.ACTIVE,
    )
    return active_classrooms_count >= plan.max_active_classrooms


class ActiveClassroomsLimitResponses(Responses):
    ACTIVE_CLASSROOMS_LIMIT_REACHED = (
        status.HTTP_409_CONFLICT,
        "Active classrooms limit reached",
    )


async def ensure_tutor_is_under_active_classrooms_limit(tutor_id: int) -> None:
    if await has_tutor_reached_active_classrooms_limit(tutor_id=tutor_id):
        raise ActiveClassroomsLimitResponses.ACTIVE_CLASSROOMS_LIMIT_REACHED
