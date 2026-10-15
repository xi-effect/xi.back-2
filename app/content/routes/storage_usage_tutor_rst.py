from pydantic import BaseModel

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.models.files_db import File
from app.content.models.ydocs_db import YDoc

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
    total_file_bytes = await File.sum_by_kwargs(
        File.size_bytes,
        owner_id=auth_data.user_id,
    )
    total_ydoc_bytes = await YDoc.sum_by_kwargs(
        YDoc.size_bytes,
        owner_id=auth_data.user_id,
    )
    return StorageUsageResponseSchema(
        total_storage_bytes=total_file_bytes + total_ydoc_bytes,
    )
