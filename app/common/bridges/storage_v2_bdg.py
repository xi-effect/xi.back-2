from httpx import AsyncClient, Response
from pydantic import BaseModel, TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings


class AccessGroupMetaSchema(BaseModel):
    id: str


class YDocMetaSchema(BaseModel):
    id: str


class StorageV2Bridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/storage-service/v2",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(AccessGroupMetaSchema))
    async def create_access_group(self) -> Response:
        return await self.client.post("/access-groups/")

    async def delete_access_group(self, access_group_id: str) -> None:
        response = await self.client.delete(f"/access-groups/{access_group_id}/")
        response.raise_for_status()

    @validate_json_response(TypeAdapter(YDocMetaSchema))
    async def create_ydoc(self, access_group_id: str) -> Response:
        return await self.client.post(f"/access-groups/{access_group_id}/ydocs/")
