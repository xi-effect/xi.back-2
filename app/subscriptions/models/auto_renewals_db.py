from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod


class AutoRenewal(Base):
    __tablename__ = "auto_renewals"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    provider_payment_method_id: Mapped[str] = mapped_column(String(50))
    renewal_period: Mapped[SubscriptionPeriod] = mapped_column(Enum(SubscriptionPeriod))

    ResponseSchema = MappedModel.create(columns=[renewal_period])

    @classmethod
    async def upsert_by_user_id(
        cls,
        user_id: int,
        provider_payment_method_id: str,
        renewal_period: SubscriptionPeriod,
    ) -> None:
        stmt = (
            insert(cls)
            .values(
                user_id=user_id,
                provider_payment_method_id=provider_payment_method_id,
                renewal_period=renewal_period,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "provider_payment_method_id": provider_payment_method_id,
                    "renewal_period": renewal_period,
                },
            )
        )
        await db.session.execute(stmt)

    @classmethod
    async def delete_by_user_id(cls, user_id: int) -> None:
        await cls.delete_by_kwargs(user_id=user_id)
