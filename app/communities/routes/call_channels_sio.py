from livekit.api import AccessToken, VideoGrants  # type: ignore[attr-defined]

from app.common.config import settings
from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.call_channels_sio_dep import CallChannelByIds
from app.communities.dependencies.communities_sio_dep import (
    current_participant_dependency,
)

router = EventRouterExt(tags=["call-channels"])


@router.on(
    "generate-livekit-token",
    summary="Generate a new livekit token for current user",
    dependencies=[current_participant_dependency],
)
async def generate_livekit_token(
    call_channel: CallChannelByIds, user: AuthorizedUser
) -> str:
    return (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(str(user.user_id))
        .with_name(user.username)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=f"call-channel-room-{call_channel.id}",
            )
        )
    ).to_jwt()
