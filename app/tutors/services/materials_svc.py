from app.common.config_bdg import storage_bridge
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.tutors.models.materials_db import Material


async def create_material(
    input_data: Material.InputSchema, auth_data: ProxyAuthData
) -> Material:
    ydoc = await storage_bridge.create_personal_ydoc(auth_data=auth_data)
    return await Material.create(
        **input_data.model_dump(), tutor_id=auth_data.user_id, ydoc_id=str(ydoc.id)
    )


async def delete_material(material: Material) -> None:
    await storage_bridge.delete_ydoc(ydoc_id=material.ydoc_id)

    await material.delete()
