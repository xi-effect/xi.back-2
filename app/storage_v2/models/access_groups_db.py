from typing import Self
from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
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
