from typing import Annotated

from pydantic_marshals.base import CompositeMarshalModel

from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.dependencies.subscriptions_dep import MySubscription
from app.subscriptions.models.auto_renewals_db import AutoRenewal
from app.subscriptions.models.subscriptions_db import Subscription

router = APIRouterExt(tags=["subscriptions"])


class DetailedSubscriptionSchema(CompositeMarshalModel):
    subscription: Annotated[Subscription, Subscription.ResponseSchema]
    auto_renewal: Annotated[AutoRenewal, AutoRenewal.ResponseSchema] | None


@router.get(
    "/users/current/subscription/",
    response_model=DetailedSubscriptionSchema.build_marshal(),
    summary="Retrieve current user's subscription",
)
async def retrieve_current_subscription(
    subscription: MySubscription,
) -> DetailedSubscriptionSchema:
    return DetailedSubscriptionSchema(
        subscription=subscription,
        auto_renewal=await AutoRenewal.find_first_by_id(subscription.user_id),
    )
