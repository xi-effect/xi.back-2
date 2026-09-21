from enum import StrEnum, auto
from uuid import uuid4

from pydantic import BaseModel
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.models.subscriptions_db import SubscriptionPlanKind

router = APIRouterExt(tags=["payments"])


class SubscriptionPeriod(StrEnum):
    MONTHLY = auto()
    YEARLY = auto()


PERIOD_TO_SUBSCRIPTION_DAYS: dict[SubscriptionPeriod, int] = {
    SubscriptionPeriod.MONTHLY: 30,
    SubscriptionPeriod.YEARLY: 365,
}

PLAN_TO_PERIOD_TO_PRICE: dict[SubscriptionPlanKind, dict[SubscriptionPeriod, int]] = {
    SubscriptionPlanKind.PRO: {
        SubscriptionPeriod.MONTHLY: 1499,
        SubscriptionPeriod.YEARLY: 14999,
    },
}


class PaymentInputSchema(BaseModel):
    period: SubscriptionPeriod


@router.post(
    path="/users/current/payments/",
    status_code=status.HTTP_201_CREATED,
    response_model=Payment.ResponseSchema,
    summary="Create a new payment for the current user",
)
async def create_payment(
    auth_data: AuthorizationData,
    data: PaymentInputSchema,
) -> Payment:
    payment_id = uuid4()
    return await Payment.create(
        id=payment_id,
        user_id=auth_data.user_id,
        # TODO (275) replace with YooKassa's real payment id
        provider_payment_id=str(payment_id),
        amount_roubles=PLAN_TO_PERIOD_TO_PRICE[SubscriptionPlanKind.PRO][data.period],
        subscription_days=PERIOD_TO_SUBSCRIPTION_DAYS[data.period],
    )
