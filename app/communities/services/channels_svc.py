from app.common.config_bdg import messenger_bridge, posts_bridge
from app.common.schemas.messenger_sch import ChatAccessKind
from app.communities.models.call_channels_db import CallChannel
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.chat_channels_db import ChatChannel
from app.communities.models.task_channels_db import TaskChannel


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
        case ChannelType.TASKS:
            await TaskChannel.create(id=channel.id)
        case ChannelType.CHAT:
            chat = await messenger_bridge.create_chat(
                access_kind=ChatAccessKind.CHAT_CHANNEL, related_id=channel.id
            )
            await ChatChannel.create(id=channel.id, chat_id=chat.id)
        case ChannelType.CALL:
            await CallChannel.create(id=channel.id)

    return channel


async def delete_channel(channel: Channel) -> None:
    match channel.kind:
        case ChannelType.POSTS:
            await posts_bridge.delete_post_channel(channel_id=channel.id)
        case ChannelType.TASKS:
            pass
        case ChannelType.CHAT:
            chat_channel = await ChatChannel.find_first_by_id(channel.id)
            if chat_channel is not None:
                await messenger_bridge.delete_chat(chat_id=chat_channel.chat_id)
        case ChannelType.CALL:
            pass

    await channel.delete()
