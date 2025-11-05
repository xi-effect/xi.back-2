from typing import Self
from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, insert, literal, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.storage_v2.models.files_db import File
from app.storage_v2.models.ydocs_db import YDoc


class AccessGroup(Base):
    __tablename__ = "access_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    ResponseSchema = MappedModel.create(columns=[id])


class AccessGroupYDoc(Base):
    __tablename__ = "access_group_ydocs"

    access_group_id: Mapped[UUID] = mapped_column(
        ForeignKey(AccessGroup.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    ydoc_id: Mapped[UUID] = mapped_column(
        ForeignKey(YDoc.id),
        primary_key=True,
        index=True,
    )

    @classmethod
    async def find_by_ids(cls, access_group_id: UUID, ydoc_id: UUID) -> Self | None:
        return await cls.find_first_by_kwargs(
            access_group_id=access_group_id,
            ydoc_id=ydoc_id,
        )

    @classmethod
    async def duplicate_all_ydocs_by_access_group(
        cls,
        source_access_group_id: UUID,
        target_access_group_id: UUID,
    ) -> None:
        ydoc_ids = await db.get_all(
            insert(YDoc)
            .from_select(
                [YDoc.content],
                (
                    select(YDoc.content)
                    .join(cls)
                    .filter_by(access_group_id=source_access_group_id)
                ),
            )
            .returning(YDoc.id)
        )

        if len(ydoc_ids) == 0:
            return
        await db.session.execute(
            insert(cls),
            [
                {"ydoc_id": ydoc_id, "access_group_id": target_access_group_id}
                for ydoc_id in ydoc_ids
            ],
        )


class AccessGroupFile(Base):
    __tablename__ = "access_group_files"

    access_group_id: Mapped[UUID] = mapped_column(
        ForeignKey(AccessGroup.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey(File.id),
        primary_key=True,
        index=True,
    )

    @classmethod
    async def find_by_ids(cls, access_group_id: UUID, file_id: UUID) -> Self | None:
        return await cls.find_first_by_kwargs(
            access_group_id=access_group_id,
            file_id=file_id,
        )

    @classmethod
    async def duplicate_all_links_by_access_group(
        cls,
        source_access_group_id: UUID,
        target_access_group_id: UUID,
    ) -> None:
        await db.session.execute(
            insert(cls).from_select(
                [cls.access_group_id, cls.file_id],
                (
                    select(literal(target_access_group_id), cls.file_id)
                    .select_from(cls)
                    .filter_by(access_group_id=source_access_group_id)
                ),
            )
        )
