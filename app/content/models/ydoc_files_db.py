from typing import Self
from uuid import UUID

from sqlalchemy import ForeignKey, insert, literal, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.content.models.files_db import File
from app.content.models.ydocs_db import YDoc


class YDocFile(Base):
    __tablename__ = "ydoc_files"

    ydoc_id: Mapped[UUID] = mapped_column(
        ForeignKey(YDoc.id, ondelete="CASCADE"),
        primary_key=True,
    )
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey(File.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    @classmethod
    async def find_first_by_ids(cls, ydoc_id: UUID, file_id: UUID) -> Self | None:
        return await cls.find_first_by_kwargs(ydoc_id=ydoc_id, file_id=file_id)

    @classmethod
    async def duplicate_all_links_by_ydoc_id(
        cls,
        source_ydoc_id: UUID,
        target_ydoc_id: UUID,
    ) -> None:
        await db.session.execute(
            insert(cls).from_select(
                [cls.ydoc_id, cls.file_id],
                (
                    select(literal(target_ydoc_id), cls.file_id)
                    .select_from(cls)
                    .filter_by(ydoc_id=source_ydoc_id)
                ),
            )
        )
