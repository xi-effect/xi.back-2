from faststream.redis import RedisRouter

from app.classrooms.models.classrooms_db import Classroom
from app.common.config import settings
from app.common.config_bdg import subscriptions_bridge
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.subscriptions_sch import UserPlanUpdateEventSchema

router = RedisRouter()


@router.subscriber(  # type: ignore[misc]  # bad typing in faststream
    stream=build_stream_sub(
        stream_name=settings.user_plans_updated_stream_name,
        service_name="classroom-service",
    ),
)
async def sync_classroom_locks_with_user_plan(data: UserPlanUpdateEventSchema) -> None:
    plan = await subscriptions_bridge.retrieve_user_plan(user_id=data.user_id)

    if plan.kind is None:
        await Classroom.lock_all_active_classrooms_by_tutor_id(tutor_id=data.user_id)
    else:
        active_classrooms_count = await Classroom.count_active_classrooms_by_tutor_id(
            tutor_id=data.user_id
        )
        await Classroom.unlock_classrooms_by_tutor_id(
            tutor_id=data.user_id,
            limit=max(plan.max_active_classrooms - active_classrooms_count, 0),
        )
