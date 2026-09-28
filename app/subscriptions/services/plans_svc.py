from typing import assert_never

from app.common.schemas.subscriptions_sch import PaidPlanKind, PlanKind, PlanSchema
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.subscriptions_db import Subscription

FREE_PLAN = PlanSchema(
    kind=None,
    max_active_classrooms=3,
    max_total_storage_bytes=500 * 1024**2,
)
PRO_PLAN = PlanSchema(
    kind=PaidPlanKind.PRO,
    max_active_classrooms=60,
    max_total_storage_bytes=20 * 1024**3,
)


async def retrieve_plan_by_user_id(user_id: int) -> PlanSchema:
    subscription = await Subscription.find_first_by_id(user_id)

    kind: PlanKind = None
    if subscription is not None and subscription.ends_at > datetime_utc_now():
        kind = subscription.plan_kind

    match kind:
        case None:
            return FREE_PLAN
        case PaidPlanKind.PRO:
            return PRO_PLAN
        case _:
            assert_never(kind)
