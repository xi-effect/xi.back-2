from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.payments.dependencies.payments_dep import PaymentById
from app.payments.dependencies.user_payments_dep import AllUserPaymentsById
from app.payments.models.payment_db import Payment

router = APIRouterExt(tags=["payments"])


@router.post(
    path="/payments/",
    status_code=status.HTTP_201_CREATED,
    response_model=Payment.ResponseSchema,
    summary="Create a new payment for current user",
)
async def create_payment(
    auth_data: AuthorizationData, data: Payment.InputSchema
) -> Payment:
    return await Payment.create(tutor_id=auth_data.user_id, **data.model_dump())


@router.get(
    path="/payments/",
    status_code=status.HTTP_200_OK,
    summary="List all current user's payments",
    response_model=list[Payment.ResponseSchema],
)
async def get_payment(
    all_user_payments: AllUserPaymentsById,
) -> list[Payment]:
    return all_user_payments


@router.patch(
    path="/payments/{payment_id}/",
    status_code=status.HTTP_200_OK,
    response_model=Payment.ResponseSchema,
    summary="Update current user's payment's data by id",
)
async def patch_payment(payment: PaymentById, data: Payment.PatchSchema) -> Payment:
    payment.update(**data.model_dump(exclude_defaults=True))
    return payment


@router.delete(
    path="/payments/{payment_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user's payment by id",
)
async def delete_payment(payment: PaymentById) -> None:
    await payment.delete()
