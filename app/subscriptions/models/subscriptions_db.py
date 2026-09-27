from datetime import datetime, timedelta

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, func, literal
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    plan_kind: Mapped[PaidPlanKind] = mapped_column(Enum(PaidPlanKind))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    ResponseSchema = MappedModel.create(columns=[plan_kind, (ends_at, AwareDatetime)])

    @classmethod
    async def add_subscription_days_by_user_id(
        cls,
        user_id: int,
        subscription_days: int,
    ) -> None:
        current_timestamp = datetime_utc_now()
        subscription_period = timedelta(days=subscription_days)
        stmt = (
            insert(cls)
            .values(
                user_id=user_id,
                plan_kind=PaidPlanKind.PRO,
                ends_at=current_timestamp + subscription_period,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                # TODO update plan_kind on conflict once there is more than one plan kind
                set_={
                    "ends_at": func.greatest(
                        cls.ends_at,
                        literal(current_timestamp, DateTime(timezone=True)),
                        type_=DateTime(timezone=True),
                    )
                    + subscription_period,
                },
            )
        )
        await db.session.execute(stmt)
