from httpx import Response
from pydantic import BaseModel, TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.storage_sch import StorageAccessGroupKind


class AccessGroupMetaSchema(BaseModel):
    id: str
    kind: StorageAccessGroupKind
    related_id: str


class YDocMetaSchema(BaseModel):
    id: str


class StorageBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/storage-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(AccessGroupMetaSchema))
    async def create_access_group(
        self, kind: StorageAccessGroupKind, related_id: int | str
    ) -> Response:
        return await self.client.post(
            "/access-groups/",
            json={
                "kind": kind,
                "related_id": str(related_id),
            },
        )

    async def delete_access_group(self, access_group_id: str) -> None:
        response = await self.client.delete(f"/access-groups/{access_group_id}/")
        response.raise_for_status()

    @validate_json_response(TypeAdapter(YDocMetaSchema))
    async def create_ydoc(self, access_group_id: str) -> Response:
        return await self.client.post(f"/access-groups/{access_group_id}/ydocs/")

    @validate_json_response(TypeAdapter(YDocMetaSchema))
    async def create_personal_ydoc(self, auth_data: ProxyAuthData) -> Response:
        return await self.client.post(
            "/access-groups/personal/ydocs/", headers=auth_data.as_headers
        )

    async def delete_ydoc(self, ydoc_id: str) -> None:
        response = await self.client.delete(f"/ydocs/{ydoc_id}/")
        response.raise_for_status()
