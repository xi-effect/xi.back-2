from httpx import AsyncClient, Response
from pydantic import TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.common.schemas.user_contacts_sch import UserContactSchema


class NotificationsBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/notification-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(list[UserContactSchema]))
    async def list_user_contacts(
        self, user_id: int, public_only: bool = False
    ) -> Response:
        return await self.client.get(
            f"/users/{user_id}/contacts/",
            params={"public_only": public_only},
        )
