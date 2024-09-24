from httpx import AsyncClient, Response
from pydantic import BaseModel, TypeAdapter

from app.common.access import AccessGroupKind
from app.common.bridges.utils import validate_json_response
from app.common.config import API_KEY, BRIDGE_BASE_URL


class AccessGroupMetaSchema(BaseModel):
    id: str
    kind: AccessGroupKind
    related_id: str


class YDocMetaSchema(BaseModel):
    id: str


class StorageBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{BRIDGE_BASE_URL}/internal/storage-service",
            headers={"X-Api-Key": API_KEY},
        )

    @validate_json_response(TypeAdapter(AccessGroupMetaSchema))
    async def create_access_group(
        self, kind: AccessGroupKind, related_id: int | str
    ) -> Response:
        return await self.client.post(
            "/access-groups/",
            json={
                "kind": kind,
                "related_id": str(related_id),
            },
        )

    async def delete_access_group(self, access_group_id: str) -> None:
        await self.client.delete(f"/access-groups/{access_group_id}/")

    @validate_json_response(TypeAdapter(YDocMetaSchema))
    async def create_ydoc(self, access_group_id: str) -> Response:
        return await self.client.post(f"/access-groups/{access_group_id}/ydocs/")
