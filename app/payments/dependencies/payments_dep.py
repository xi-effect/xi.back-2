from typing import Annotated

from fastapi import Depends, Path

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.payments.models.payment_db import Payment


class PaymentResponses(Responses):
    PAYMENT_DELETED = 200, "Payment successfully deleted"
    NOT_YOUR_PAYMENT = 403, "Not your payment"
    PAYMENT_NOT_FOUND = 404, "Payment not found"


@with_responses(PaymentResponses)
async def get_payment_by_ids(payment_id: Annotated[int, Path()]) -> Payment:
    payment = await Payment.find_first_by_id(payment_id)
    if payment is None:
        raise PaymentResponses.PAYMENT_NOT_FOUND
    return payment


PaymentByIds = Annotated[Payment, Depends(get_payment_by_ids)]


@with_responses(PaymentResponses)
async def delete_payment_by_ids(
    payment: PaymentByIds, auth_data: AuthorizationData
) -> None:
    if payment.tutor_id != auth_data.user_id:
        raise PaymentResponses.NOT_YOUR_PAYMENT
    await payment.delete()
    raise PaymentResponses.PAYMENT_DELETED


DeletePaymentByIds = Annotated[PaymentResponses, Depends(delete_payment_by_ids)]


@with_responses(PaymentResponses)
async def patch_payment_by_ids(
    payment: PaymentByIds, auth_data: AuthorizationData, patch_data: Payment.PatchSchema
) -> Payment:
    if payment.tutor_id != auth_data.user_id:
        raise PaymentResponses.NOT_YOUR_PAYMENT
    payment.update(**patch_data.model_dump(exclude_defaults=True))
    return payment


PatchPaymentByIds = Annotated[Payment, Depends(patch_payment_by_ids)]
