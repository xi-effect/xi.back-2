from httpx import Response

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_external_json_response
from app.common.config import settings


class PostsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/post-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_external_json_response()
    async def create_post_channel(self, channel_id: int, community_id: int) -> Response:
        return await self.client.post(
            f"/post-channels/{channel_id}/",
            json={"community_id": community_id},
        )

    @validate_external_json_response()
    async def delete_post_channel(self, channel_id: int) -> Response:
        return await self.client.delete(f"/post-channels/{channel_id}/")
