from enum import StrEnum, auto
from typing import Annotated, Final
from uuid import UUID, uuid4

from pydantic import BaseModel
from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.config import settings
from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.subscriptions.config import yookassa_client
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaAmountSchema,
    YooKassaCreatePaymentRequestSchema,
    YooKassaReceiptCustomerSchema,
    YooKassaReceiptItemSchema,
    YooKassaReceiptSchema,
    YooKassaRedirectConfirmationSchema,
)

router = APIRouterExt(tags=["payments"])


class SubscriptionPeriod(StrEnum):
    MONTHLY = auto()
    YEARLY = auto()


PERIOD_TO_SUBSCRIPTION_DAYS: dict[SubscriptionPeriod, int] = {
    SubscriptionPeriod.MONTHLY: 30,
    SubscriptionPeriod.YEARLY: 365,
}

PLAN_TO_PERIOD_TO_PRICE: dict[PaidPlanKind, dict[SubscriptionPeriod, int]] = {
    PaidPlanKind.PRO: {
        SubscriptionPeriod.MONTHLY: 1499,
        SubscriptionPeriod.YEARLY: 14999,
    },
}

RECEIPT_ITEM_DESCRIPTION_TEMPLATE: Final[str] = (
    "Подписка PRO на {subscription_days} дней"
)


class PaymentInputSchema(BaseModel):
    period: SubscriptionPeriod


class PaymentCorrelationSchema(BaseModel):
    payment_id: UUID


class CheckoutSchema(CompositeMarshalModel):
    payment: Annotated[Payment, Payment.ResponseSchema]
    confirmation_url: str


@router.post(
    path="/users/current/payments/",
    status_code=status.HTTP_201_CREATED,
    response_model=CheckoutSchema.build_marshal(),
    summary="Create a new payment for the current user",
)
async def create_payment(
    auth_data: AuthorizationData,
    data: PaymentInputSchema,
) -> CheckoutSchema:
    payment_id = uuid4()
    amount_roubles = PLAN_TO_PERIOD_TO_PRICE[PaidPlanKind.PRO][data.period]
    subscription_days = PERIOD_TO_SUBSCRIPTION_DAYS[data.period]

    user = await users_internal_bridge.retrieve_user(user_id=auth_data.user_id)

    amount = YooKassaAmountSchema(value=f"{amount_roubles:.2f}")
    yookassa_payment = await yookassa_client.create_payment(
        data=YooKassaCreatePaymentRequestSchema[PaymentCorrelationSchema](
            amount=amount,
            confirmation=YooKassaRedirectConfirmationSchema(
                return_url=settings.yookassa_return_url
            ),
            receipt=YooKassaReceiptSchema(
                customer=YooKassaReceiptCustomerSchema(email=user.email),
                items=[
                    YooKassaReceiptItemSchema(
                        description=RECEIPT_ITEM_DESCRIPTION_TEMPLATE.format(
                            subscription_days=subscription_days
                        ),
                        amount=amount,
                    )
                ],
            ),
            metadata=PaymentCorrelationSchema(payment_id=payment_id),
        ),
        idempotence_key=str(payment_id),
    )

    payment = await Payment.create(
        id=payment_id,
        user_id=auth_data.user_id,
        provider_payment_id=yookassa_payment.id,
        amount_roubles=amount_roubles,
        subscription_days=subscription_days,
    )
    return CheckoutSchema(
        payment=payment,
        confirmation_url=yookassa_payment.confirmation.confirmation_url,
    )
