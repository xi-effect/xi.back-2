from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.dependencies.subscriptions_dep import MySubscription
from app.subscriptions.models.subscriptions_db import Subscription

router = APIRouterExt(tags=["subscriptions"])


@router.get(
    "/users/current/subscription/",
    response_model=Subscription.ResponseSchema,
    summary="Retrieve current user's subscription",
)
async def retrieve_current_subscription(subscription: MySubscription) -> Subscription:
    return subscription
