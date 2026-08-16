from httpx import Response

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings


class PostsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/post-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def create_post_channel(self, channel_id: int, community_id: int) -> Response:
        return await ResponsePipelineBuilder.initialize_from_request(
            self.client.post(
                f"/post-channels/{channel_id}/",
                json={"community_id": community_id},
            )
        ).validate_status_code()

    async def delete_post_channel(self, channel_id: int) -> Response:
        return await ResponsePipelineBuilder.initialize_from_request(
            self.client.delete(f"/post-channels/{channel_id}/")
        ).validate_status_code()
