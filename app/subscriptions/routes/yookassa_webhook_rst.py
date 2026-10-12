from typing import assert_never

from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.config import yookassa_client
from app.subscriptions.models.auto_renewals_db import AutoRenewal
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.models.subscriptions_db import Subscription
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaCanceledPaymentSchema,
    YooKassaEventSchema,
    YooKassaEventType,
    YooKassaPendingPaymentSchema,
    YooKassaSucceededPaymentSchema,
    YooKassaWaitingForCapturePaymentSchema,
)

router = APIRouterExt()


class SucceededPaymentNotFoundException(Exception):
    pass


async def handle_succeeded_payment(
    yookassa_payment: YooKassaSucceededPaymentSchema,
) -> None:
    payment_id = yookassa_payment.metadata.payment_id
    payment = await Payment.find_and_complete_by_id(payment_id=payment_id)
    if payment is None:
        if not await Payment.is_present_by_id(payment_id=payment_id):
            raise SucceededPaymentNotFoundException(payment_id)
        return  # the payment was already completed, the event is a repeated one

    await Subscription.add_subscription_days_by_user_id(
        user_id=payment.user_id,
        subscription_days=payment.subscription_days,
    )

    if (
        yookassa_payment.metadata.auto_renewal_period is not None
        and yookassa_payment.payment_method is not None
        and yookassa_payment.payment_method.saved
    ):
        await AutoRenewal.upsert_by_user_id(
            user_id=payment.user_id,
            provider_payment_method_id=yookassa_payment.payment_method.id,
            renewal_period=yookassa_payment.metadata.auto_renewal_period,
        )
    else:
        await AutoRenewal.delete_by_user_id(user_id=payment.user_id)


async def handle_canceled_payment(
    yookassa_payment: YooKassaCanceledPaymentSchema,
) -> None:
    await Payment.find_and_complete_by_id(
        payment_id=yookassa_payment.metadata.payment_id,
        cancellation_reason=yookassa_payment.cancellation_details.reason,
    )


class UnexpectedYooKassaEventException(Exception):
    pass


class InvalidPaymentStatusException(Exception):
    pass


@router.post(
    path="/yookassa-events/",
    summary="Execute YooKassa webhook for payments",
)
async def handle_event_from_yookassa(event: YooKassaEventSchema) -> None:
    if event.event not in YooKassaEventType:
        raise UnexpectedYooKassaEventException(event.event)

    yookassa_payment = await yookassa_client.retrieve_payment(
        provider_payment_id=event.object.id
    )

    match yookassa_payment:
        case YooKassaSucceededPaymentSchema():
            await handle_succeeded_payment(yookassa_payment)
        case YooKassaCanceledPaymentSchema():
            await handle_canceled_payment(yookassa_payment)
        case YooKassaPendingPaymentSchema() | YooKassaWaitingForCapturePaymentSchema():
            raise InvalidPaymentStatusException(yookassa_payment.status)
        case _:
            assert_never(yookassa_payment)
