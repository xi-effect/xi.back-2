from httpx import AsyncClient, Response
from pydantic import TypeAdapter

from app.common.access import AccessLevel
from app.common.bridges.utils import validate_json_response
from app.common.config import API_KEY, BRIDGE_BASE_URL
from app.common.dependencies.authorization_dep import ProxyAuthData


class CommunitiesBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{BRIDGE_BASE_URL}/internal/community-service",
            headers={"X-Api-Key": API_KEY},
        )

    @validate_json_response(TypeAdapter(AccessLevel))
    async def retrieve_board_channel_access_level(
        self, board_channel_id: int | str, auth_data: ProxyAuthData
    ) -> Response:
        return await self.client.get(
            f"/channels/{board_channel_id}/board/access-level/",
            headers=auth_data.as_headers,
        )
