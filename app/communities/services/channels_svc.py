from app.common.config_bdg import posts_bridge
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.channels_db import Channel, ChannelType


async def create_channel(
    community_id: int, category_id: int | None, data: Channel.InputSchema
) -> Channel:
    channel = await Channel.create(
        community_id=community_id,
        category_id=category_id,
        **data.model_dump(),
    )

    match channel.kind:
        case ChannelType.POSTS:
            await posts_bridge.create_post_channel(channel.id, channel.community_id)
        case ChannelType.BOARD:
            await BoardChannel.create(id=channel.id)

    return channel


async def delete_channel(channel: Channel) -> None:
    match channel.kind:
        case ChannelType.POSTS:
            await posts_bridge.delete_post_channel(channel.id)
        case ChannelType.BOARD:
            pass
    await channel.delete()
