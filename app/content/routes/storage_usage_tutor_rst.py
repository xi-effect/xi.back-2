from pydantic import BaseModel

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.services import storage_svc

router = APIRouterExt(tags=["storage usage"])


class StorageUsageResponseSchema(BaseModel):
    total_storage_bytes: int


@router.get(
    path="/roles/tutor/storage-usage/",
    summary="Retrieve storage usage for the current user",
)
async def retrieve_storage_usage(
    auth_data: AuthorizationData,
) -> StorageUsageResponseSchema:
    return StorageUsageResponseSchema(
        total_storage_bytes=await storage_svc.compute_storage_usage_by_owner_id(
            owner_id=auth_data.user_id,
        ),
    )
