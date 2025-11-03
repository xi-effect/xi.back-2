from httpx import Response
from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.common.schemas.users_sch import UserProfileSchema


class UsersInternalBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/user-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(dict[int, UserProfileSchema]))
    async def retrieve_multiple_users(self, user_ids: list[int]) -> Response:
        return await self.client.get(
            "/users/",
            params={"user_ids": user_ids},
        )

    @validate_json_response(TypeAdapter(UserProfileSchema))
    async def retrieve_user(self, user_id: int) -> Response:
        return await self.client.get(f"/users/{user_id}/")
