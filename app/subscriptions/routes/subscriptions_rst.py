from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.dependencies.subscriptions_dep import CurrentActiveSubscription
from app.subscriptions.models.subscriptions_db import Subscription

router = APIRouterExt(tags=["subscriptions"])


@router.get(
    "/users/current/subscription/",
    response_model=Subscription.ResponseSchema,
    summary="Retrieve current user's active subscription",
)
async def retrieve_current_subscription(
    subscription: CurrentActiveSubscription,
) -> Subscription:
    return subscription
