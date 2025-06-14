from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.payments.dependencies.payments_dep import DeletePaymentByIds, PatchPaymentByIds
from app.payments.dependencies.user_payments_dep import AllUserPaymentsByIds
from app.payments.models.payment_db import Payment

router = APIRouterExt(tags=["payments"])


@router.post(
    path="/payment",
    status_code=201,
    response_model=Payment.ResponseSchema,
    summary="Create a new payment in payments history",
)
async def create_payment(
    auth_data: AuthorizationData, data: Payment.InputSchema
) -> Payment:
    return await Payment.create(tutor_id=auth_data.user_id, **data.model_dump())


@router.patch(
    path="/payment/{payment_id}",
    status_code=200,
    response_model=Payment.ResponseSchema,
    summary="Change payments data",
)
async def patch_payment(payment: PatchPaymentByIds) -> Payment:
    return payment


@router.delete(
    path="/payment/{payment_id}", status_code=200, summary="Delete payment by id"
)
async def delete_payment(response: DeletePaymentByIds) -> None: ...


@router.get(
    path="/payment",
    status_code=200,
    summary="Get current users payments list",
    response_model=None,
)
async def get_payment(
    all_user_payments: AllUserPaymentsByIds,
) -> list[Payment]:
    return all_user_payments
