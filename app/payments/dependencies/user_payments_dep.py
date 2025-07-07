from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, Query
from pydantic import AwareDatetime
from sqlalchemy import select

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.sqlalchemy_ext import db
from app.payments.models.payment_db import Payment


async def get_all_user_payments_by_id(
    auth_data: AuthorizationData,
    payed_after: Annotated[AwareDatetime, Query()],
    payed_before: Annotated[AwareDatetime, Query()],
) -> Sequence[Payment]:
    stmt = (
        select(Payment)
        .where(
            Payment.tutor_id == auth_data.user_id,
            Payment.payed_at >= payed_after,
            Payment.payed_at < payed_before,
        )
        .order_by(Payment.payed_at.desc())
    )
    payments = await db.get_all(stmt)
    if not payments:
        return []
    return payments


AllUserPaymentsById = Annotated[list[Payment], Depends(get_all_user_payments_by_id)]
