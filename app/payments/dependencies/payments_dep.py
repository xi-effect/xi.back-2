from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.payments.models.payment_db import Payment


class PaymentResponses(Responses):
    ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Payment access denied"
    PAYMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Payment not found"


@with_responses(PaymentResponses)
async def get_payment_by_id(
    payment_id: Annotated[int, Path()], auth_data: AuthorizationData
) -> Payment:
    payment = await Payment.find_first_by_id(payment_id)
    if payment is None:
        raise PaymentResponses.PAYMENT_NOT_FOUND
    if payment.tutor_id != auth_data.user_id:
        raise PaymentResponses.ACCESS_DENIED
    return payment


PaymentById = Annotated[Payment, Depends(get_payment_by_id)]
