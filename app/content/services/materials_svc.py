from app.common.config import content_token_provider
from app.common.schemas.content_sch import (
    ContentTokenPayloadSchema,
    ContentYDocItemSchema,
    YDocAccessLevel,
)
from app.content.models.materials_db import Material


def build_ydoc_item(
    material: Material,
    user_id: int,
    can_upload_files: bool,
    ydoc_access_level: YDocAccessLevel,
) -> ContentYDocItemSchema:
    return ContentYDocItemSchema(
        ydoc_id=material.main_ydoc_id,
        content_token=content_token_provider.serialize_and_sign(
            ContentTokenPayloadSchema(
                material_id=material.id,
                ydoc_id=material.main_ydoc_id,
                user_id=user_id,
                can_upload_files=can_upload_files,
                can_read_files=True,
                ydoc_access_level=ydoc_access_level,
            )
        ),
    )
