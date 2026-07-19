from httpx import Response
from pydantic import BaseModel, TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.messenger_sch import ChatAccessKind


class ChatMetaSchema(BaseModel):
    id: int
    access_kind: ChatAccessKind
    related_id: str


chat_meta_type_adapter = TypeAdapter(ChatMetaSchema)


class MessengerBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/messenger-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def create_chat(
        self, access_kind: ChatAccessKind, related_id: int | str
    ) -> ChatMetaSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.post(
                    "/chats/",
                    json={
                        "access_kind": access_kind,
                        "related_id": str(related_id),
                    },
                )
            )
            .validate_status_code()
            .validate_json(chat_meta_type_adapter)
        )

    async def delete_chat(self, chat_id: int) -> Response:
        return await ResponsePipelineBuilder.initialize_from_request(
            self.client.delete(f"/chats/{chat_id}/")
        ).validate_status_code()
