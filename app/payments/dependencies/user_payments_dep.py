from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy import select

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.sqlalchemy_ext import db
from app.payments.models.payment_db import Payment


class UserPaymentResponses(Responses):
    USER_PAYMENT_NOT_FOUND = 404, "User payment not found"


@with_responses(UserPaymentResponses)
async def get_all_user_payments_by_ids(
    auth_data: AuthorizationData,
    payed_after: Annotated[datetime, Query()],
    payed_before: Annotated[datetime, Query()],
) -> Sequence[Payment]:
    stmt = (
        select(Payment)
        .where(
            Payment.tutor_id == auth_data.user_id,
            Payment.payed_at > payed_after,
            Payment.payed_at < payed_before,
        )
        .order_by(Payment.payed_at.desc())
    )
    payments = await db.get_all(stmt)
    if not payments:
        raise UserPaymentResponses.USER_PAYMENT_NOT_FOUND
    return payments


AllUserPaymentsByIds = Annotated[list[Payment], Depends(get_all_user_payments_by_ids)]
