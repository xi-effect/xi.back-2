from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.subscriptions.models.payments_db import Payment


class PaymentResponses(Responses):
    PAYMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Payment not found"


@with_responses(PaymentResponses)
async def get_payment_by_id(payment_id: Annotated[UUID, Path()]) -> Payment:
    payment = await Payment.find_first_by_id(payment_id)
    if payment is None:
        raise PaymentResponses.PAYMENT_NOT_FOUND
    return payment


PaymentByID = Annotated[Payment, Depends(get_payment_by_id)]


class MyPaymentResponses(Responses):
    PAYMENT_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Payment access denied"


@with_responses(MyPaymentResponses)
async def get_my_payment_by_id(
    auth_data: AuthorizationData,
    payment: PaymentByID,
) -> Payment:
    if payment.user_id != auth_data.user_id:
        raise MyPaymentResponses.PAYMENT_ACCESS_DENIED
    return payment


MyPaymentByID = Annotated[Payment, Depends(get_my_payment_by_id)]
