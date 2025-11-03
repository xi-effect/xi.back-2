from app.common.config_bdg import storage_v2_bridge
from app.materials.models.materials_db import Material


async def delete_material(material: Material) -> None:
    await storage_v2_bridge.delete_access_group(
        access_group_id=material.access_group_id
    )
    await material.delete()
