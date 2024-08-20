from contextlib import AsyncExitStack

from httpx import AsyncClient

from app.common.config import API_KEY, POSTS_BASE_URL


class PostsBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{POSTS_BASE_URL}/internal/post-service",
            headers={"X-Api-Key": API_KEY},
        )
        self.is_open = False

    async def open_if_unopen(self, stack: AsyncExitStack) -> None:
        if self.is_open:
            return
        await stack.enter_async_context(self.client)
        self.is_open = True

    async def create_post_channel(self, channel_id: int, community_id: int) -> None:
        response = await self.client.post(
            f"/post-channels/{channel_id}/",
            json={"community_id": community_id},
        )
        response.raise_for_status()

    async def delete_post_channel(self, channel_id: int) -> None:
        response = await self.client.delete(f"/post-channels/{channel_id}/")
        response.raise_for_status()
