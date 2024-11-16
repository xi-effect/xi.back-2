from httpx import AsyncClient, Response
from pydantic import TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.storage_sch import YDocAccessLevel


class CommunitiesBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/community-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(YDocAccessLevel))
    async def retrieve_board_channel_access_level(
        self, board_channel_id: int | str, auth_data: ProxyAuthData
    ) -> Response:
        return await self.client.get(
            f"/channels/{board_channel_id}/board/access-level/",
            headers=auth_data.as_headers,
        )
