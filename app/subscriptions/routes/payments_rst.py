from typing import Final
from uuid import uuid4

from pydantic import BaseModel
from starlette import status

from app.common.config import settings
from app.common.config_bdg import users_internal_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.subscriptions.config import yookassa_client
from app.subscriptions.dependencies.payments_dep import MyPaymentByID
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.schemas.payments_sch import PaymentCorrelationSchema
from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaAmountSchema,
    YooKassaCreatePaymentRequestSchema,
    YooKassaReceiptCustomerSchema,
    YooKassaReceiptItemSchema,
    YooKassaReceiptSchema,
    YooKassaRedirectConfirmationSchema,
)

router = APIRouterExt(tags=["payments"])


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
    should_auto_renew: bool


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
    amount_roubles = PLAN_TO_PERIOD_TO_PRICE[PaidPlanKind.PRO][data.period]
    subscription_days = PERIOD_TO_SUBSCRIPTION_DAYS[data.period]

    user = await users_internal_bridge.retrieve_user(user_id=auth_data.user_id)

    amount = YooKassaAmountSchema(value=f"{amount_roubles:.2f}")
    yookassa_payment = await yookassa_client.create_payment(
        data=YooKassaCreatePaymentRequestSchema(
            amount=amount,
            save_payment_method=data.should_auto_renew,
            confirmation=YooKassaRedirectConfirmationSchema(
                return_url=f"{settings.yookassa_return_url}?payment_id={payment_id}"
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
            metadata=PaymentCorrelationSchema(
                payment_id=payment_id,
                auto_renewal_period=data.period if data.should_auto_renew else None,
            ),
        ),
        idempotence_key=str(payment_id),
    )

    return await Payment.create(
        id=payment_id,
        user_id=auth_data.user_id,
        provider_payment_id=yookassa_payment.id,
        amount_roubles=amount_roubles,
        subscription_days=subscription_days,
        confirmation_url=yookassa_payment.confirmation.confirmation_url,
    )


@router.get(
    path="/users/current/payments/{payment_id}/",
    response_model=Payment.ResponseSchema,
    summary="Retrieve a payment by id for the current user",
)
async def retrieve_payment(payment: MyPaymentByID) -> Payment:
    return payment
