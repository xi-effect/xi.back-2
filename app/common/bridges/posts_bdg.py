from app.common.bridges.base_bdg import BaseBridge
from app.common.config import settings


class PostsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/post-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def create_post_channel(self, channel_id: int, community_id: int) -> None:
        response = await self.client.post(
            f"/post-channels/{channel_id}/",
            json={"community_id": community_id},
        )
        response.raise_for_status()

    async def delete_post_channel(self, channel_id: int) -> None:
        response = await self.client.delete(f"/post-channels/{channel_id}/")
        response.raise_for_status()
