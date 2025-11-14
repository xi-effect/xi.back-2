from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import LargeBinary, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    content: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)

    ResponseSchema = MappedModel.create(columns=[id])

    @classmethod
    async def duplicate_by_id(cls, source_ydoc_id: UUID) -> UUID:
        stmt = (
            insert(cls)
            .from_select(
                [cls.content],
                (select(cls.content).select_from(cls).filter_by(id=source_ydoc_id)),
            )
            .returning(cls.id)
        )
        return (await db.session.execute(stmt)).scalar_one()
