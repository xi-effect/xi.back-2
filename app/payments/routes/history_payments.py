from datetime import datetime

from fastapi import HTTPException

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.payments.models.history_payments_models import Payment

router = APIRouterExt(tags=["history_payment"])


@router.post(
    "/student_id/{student_id}/amount/{amount}/date/{date}",
    status_code=201,
    response_model=Payment.ResponseSchema,
    summary="create payment",
)
async def payment(
    auth_data: AuthorizationData,
    student_id: int,
    amount: int,
    date: datetime,
) -> Payment.ResponseSchema:
    payment = await Payment.find_or_create(
        tutor_id=auth_data.user_id,
        student_id=student_id,
        payed_at=date,
        amount=amount,
    )
    return Payment.ResponseSchema.from_orm(payment)


@router.patch(
    "/payments/{payment_id}",
    status_code=200,
    response_model=Payment.ResponseSchema,
    summary="Update payment by ID",
)
async def update_payment(
    payment_id: int,
    auth_data: AuthorizationData,
    patch_data: Payment.PatchSchema,
) -> Payment.ResponseSchema:
    payment = await Payment.find_first_by_kwargs(id=payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.tutor_id != auth_data.user_id:
        raise HTTPException(
            status_code=403, detail="You do not have permission to update this payment"
        )

    updated_data = patch_data.dict(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(payment, key, value)

    # await payment.create()

    return Payment.ResponseSchema.from_orm(payment)


@router.delete(
    "/payments/{payment_id}",
    status_code=204,
    summary="Delete payment by ID",
)
async def delete_payment(
    payment_id: int,
    auth_data: AuthorizationData,
) -> None:
    payment = await Payment.find_first_by_kwargs(id=payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.tutor_id != auth_data.user_id:
        raise HTTPException(
            status_code=403, detail="You do not have permission to delete this payment"
        )

    await payment.delete()


@router.get(
    "/payments/",
    status_code=200,
    response_model=list[Payment.ResponseSchema],
    summary="Get payments created by the current user with filtering and sorting",
)
async def get_payments(
    auth_data: AuthorizationData,
    payed_after: datetime,
    payed_before: datetime,
) -> list[Payment.ResponseSchema]:
    if payed_after >= payed_before:
        raise HTTPException(
            status_code=400,
            detail="Invalid date range: payed_after must be less than payed_before",
        )

    payments = await Payment.find_all_by_kwargs(
        tutor_id=auth_data.user_id,
        payed_at__gte=payed_after,
        payed_at__lt=payed_before,
        order_by="-payed_at",
    )

    return [Payment.ResponseSchema.from_orm(payment) for payment in payments]
