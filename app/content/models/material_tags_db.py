from typing import ClassVar
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.content.models.materials_db import Material


class MaterialTag(Base):
    __tablename__ = "material_tags"

    max_count_per_material: ClassVar[int] = 5

    material_id: Mapped[UUID] = mapped_column(
        ForeignKey(Material.id, ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    async def replace_all_by_material_id(
        cls,
        material_id: UUID,
        tag_ids: set[int],
    ) -> None:
        await cls.delete_by_kwargs(material_id=material_id)
        if len(tag_ids) != 0:
            await cls.create_batch(
                {"material_id": material_id, "tag_id": tag_id} for tag_id in tag_ids
            )
