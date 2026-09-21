from datetime import timedelta
from typing import Annotated

from fastapi import Body
from starlette import status

from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.dependencies.promocodes_dep import PromocodeResponses
from app.subscriptions.models.promocode_redemptions_db import PromocodeRedemption
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription

router = APIRouterExt(tags=["promocode redemptions"])


class PromocodeRedemptionResponses(Responses):
    PROMOCODE_NOT_ACTIVE_YET = status.HTTP_409_CONFLICT, "Promocode not active yet"
    PROMOCODE_EXPIRED = status.HTTP_409_CONFLICT, "Promocode expired"
    PROMOCODE_ALREADY_REDEEMED = status.HTTP_409_CONFLICT, "Promocode already redeemed"
    PROMOCODE_USAGE_LIMIT_REACHED = (
        status.HTTP_409_CONFLICT,
        "Promocode usage limit reached",
    )
    PROMOCODE_MAX_ACCOUNT_AGE_EXCEEDED = (
        status.HTTP_409_CONFLICT,
        "Promocode max account age exceeded",
    )


@router.post(
    "/users/current/promocode-redemptions/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=Responses.chain(PromocodeResponses, PromocodeRedemptionResponses),
    summary="Redeem a promocode for the current user",
)
async def redeem_promocode(
    auth_data: AuthorizationData,
    code: Annotated[Promocode.CodeType, Body(embed=True)],
) -> None:
    promocode = await Promocode.find_first_by_kwargs(code=code)
    if promocode is None:
        raise PromocodeResponses.PROMOCODE_NOT_FOUND

    if promocode.valid_from is not None and datetime_utc_now() < promocode.valid_from:
        raise PromocodeRedemptionResponses.PROMOCODE_NOT_ACTIVE_YET
    if promocode.valid_until is not None and datetime_utc_now() > promocode.valid_until:
        raise PromocodeRedemptionResponses.PROMOCODE_EXPIRED

    if await PromocodeRedemption.is_present_by_ids(
        promocode_id=promocode.id, user_id=auth_data.user_id
    ):
        raise PromocodeRedemptionResponses.PROMOCODE_ALREADY_REDEEMED

    if (
        promocode.usage_limit is not None
        and promocode.usage_count >= promocode.usage_limit
    ):
        raise PromocodeRedemptionResponses.PROMOCODE_USAGE_LIMIT_REACHED

    if promocode.max_account_age_days is not None:
        user = await users_internal_bridge.retrieve_user(user_id=auth_data.user_id)
        if datetime_utc_now() - user.created_at > timedelta(
            days=promocode.max_account_age_days
        ):
            raise PromocodeRedemptionResponses.PROMOCODE_MAX_ACCOUNT_AGE_EXCEEDED

    if not await Promocode.has_incremented_usage_count_by_id(promocode_id=promocode.id):
        raise PromocodeRedemptionResponses.PROMOCODE_USAGE_LIMIT_REACHED
    await Subscription.add_subscription_days_by_user_id(
        user_id=auth_data.user_id, subscription_days=promocode.subscription_days
    )
    await PromocodeRedemption.create(
        promocode_id=promocode.id, user_id=auth_data.user_id
    )
