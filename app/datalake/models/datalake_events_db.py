from datetime import datetime
from uuid import UUID, uuid4

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.datalake_sch import DatalakeEventKind
from app.common.utils.datetime import datetime_utc_now


class DatalakeEvent(Base):
    __tablename__ = "datalake_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    kind: Mapped[DatalakeEventKind] = mapped_column(
        Enum(DatalakeEventKind, native_enum=False, create_constraint=False, length=100)
    )
    user_id: Mapped[int] = mapped_column()

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime_utc_now,
        index=True,
    )

    ResponseSchema = MappedModel.create(
        columns=[
            id,
            user_id,
            (recorded_at, AwareDatetime),
        ]
    )
