from httpx import AsyncClient, Response
from pydantic import BaseModel, TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.common.schemas.messenger_sch import ChatAccessKind


class ChatMetaSchema(BaseModel):
    id: int
    access_kind: ChatAccessKind
    related_id: str


class MessengerBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/messenger-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(ChatMetaSchema))
    async def create_chat(
        self, access_kind: ChatAccessKind, related_id: int | str
    ) -> Response:
        response = await self.client.post(
            "/chats/",
            json={
                "access_kind": access_kind,
                "related_id": str(related_id),
            },
        )
        response.raise_for_status()
        return response

    async def delete_chat(self, chat_id: int) -> None:
        response = await self.client.delete(f"/chats/{chat_id}/")
        response.raise_for_status()
