from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.subscriptions.models.subscriptions_db import Subscription


class SubscriptionResponses(Responses):
    SUBSCRIPTION_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Subscription not found"


@with_responses(SubscriptionResponses)
async def get_my_subscription(auth_data: AuthorizationData) -> Subscription:
    subscription = await Subscription.find_first_by_id(auth_data.user_id)
    if subscription is None:
        raise SubscriptionResponses.SUBSCRIPTION_NOT_FOUND
    return subscription


MySubscription = Annotated[Subscription, Depends(get_my_subscription)]
