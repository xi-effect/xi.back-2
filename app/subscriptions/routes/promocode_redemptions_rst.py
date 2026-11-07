from datetime import timedelta

from starlette import status

from app.common.config_bdg import subscriptions_bridge, users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.subscriptions_sch import UserPlanUpdateEventSchema
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.dependencies.promocodes_dep import PromocodeByCode
from app.subscriptions.models.promocode_redemptions_db import PromocodeRedemption
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription

router = APIRouterExt(tags=["promocode redemptions"])


class PromocodeRedemptionResponses(Responses):
    PROMOCODE_ALREADY_REDEEMED = status.HTTP_409_CONFLICT, "Promocode already redeemed"
    PROMOCODE_NOT_ACTIVE_YET = status.HTTP_409_CONFLICT, "Promocode not active yet"
    PROMOCODE_EXPIRED = status.HTTP_409_CONFLICT, "Promocode expired"
    PROMOCODE_MAX_ACCOUNT_AGE_EXCEEDED = (
        status.HTTP_409_CONFLICT,
        "Promocode max account age exceeded",
    )
    PROMOCODE_USAGE_LIMIT_REACHED = (
        status.HTTP_409_CONFLICT,
        "Promocode usage limit reached",
    )


@router.post(
    "/promocodes/{code}/redemptions/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PromocodeRedemptionResponses.responses(),
    summary="Redeem a promocode by code for the current user",
)
async def redeem_promocode(
    auth_data: AuthorizationData,
    promocode: PromocodeByCode,
) -> None:
    if (
        await PromocodeRedemption.create_by_ids(
            promocode_id=promocode.id,
            user_id=auth_data.user_id,
        )
        is None
    ):
        raise PromocodeRedemptionResponses.PROMOCODE_ALREADY_REDEEMED

    current_timestamp = datetime_utc_now()
    if promocode.valid_from is not None and current_timestamp < promocode.valid_from:
        raise PromocodeRedemptionResponses.PROMOCODE_NOT_ACTIVE_YET
    if promocode.valid_until is not None and current_timestamp > promocode.valid_until:
        raise PromocodeRedemptionResponses.PROMOCODE_EXPIRED

    if promocode.max_account_age_days is not None:
        detailed_user_data = await users_internal_bridge.retrieve_user(
            user_id=auth_data.user_id
        )
        if current_timestamp - detailed_user_data.created_at > timedelta(
            days=promocode.max_account_age_days,
        ):
            raise PromocodeRedemptionResponses.PROMOCODE_MAX_ACCOUNT_AGE_EXCEEDED

    if (
        await Promocode.find_and_increment_usage_count_by_id(promocode_id=promocode.id)
        is None
    ):
        raise PromocodeRedemptionResponses.PROMOCODE_USAGE_LIMIT_REACHED

    await Subscription.add_subscription_days_by_user_id(
        user_id=auth_data.user_id,
        subscription_days=promocode.subscription_days,
    )
    await subscriptions_bridge.publish_user_plan_update(
        UserPlanUpdateEventSchema(user_id=auth_data.user_id)
    )
