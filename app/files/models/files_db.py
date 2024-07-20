from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(unique=True)

    @classmethod
    async def get_all_files_names(cls, *order_by: Any, **kwargs: Any) -> Sequence[str]:
        files = await cls.find_all_by_kwargs(*order_by, **kwargs)
        return [file.filename for file in files]
