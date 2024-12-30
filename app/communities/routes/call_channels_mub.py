from typing import Annotated, Literal

from livekit.api import AccessToken, VideoGrants  # type: ignore[attr-defined]
from pydantic import BaseModel, Field, HttpUrl
from starlette.datastructures import URL

from app.common.config import settings
from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.call_channels_dep import CallChannelById

router = APIRouterExt(tags=["call-channels mub"])


class UserInputSchema(BaseModel):
    user_id: int
    username: str


class GrantsInputSchema(BaseModel):
    room_admin: bool = False
    can_publish: bool = True
    can_subscribe: bool = True
    can_publish_data: bool = True
    can_publish_sources: list[
        Literal["camera", "microphone", "screen_share", "screen_share_audio"]
    ] = []
    hidden: bool = False


class ConfigInputSchema(BaseModel):
    # default_factory is used to hide config secrets from API documentation
    url: Annotated[str, Field(default_factory=lambda: settings.livekit_url)]
    api_key: Annotated[str, Field(default_factory=lambda: settings.livekit_api_key)]
    api_secret: Annotated[
        str, Field(default_factory=lambda: settings.livekit_api_secret)
    ]


class TokenRequestSchema(BaseModel):
    user: UserInputSchema
    grants: Annotated[
        GrantsInputSchema,
        Field(default_factory=GrantsInputSchema, alias="grants_override"),
    ]
    config: Annotated[
        ConfigInputSchema,
        Field(default_factory=ConfigInputSchema, alias="config_override"),
    ]


class TokenResponseSchema(BaseModel):
    token: str
    demo_url: HttpUrl


@router.post(
    "/channels/{channel_id}/call/tokens/",
    summary="Generate a livekit token",
)
async def generate_livekit_token(
    call_channel: CallChannelById, data: TokenRequestSchema
) -> TokenResponseSchema:
    token: str = (
        AccessToken(
            data.config.api_key,
            data.config.api_secret,
        )
        .with_identity(str(data.user.user_id))
        .with_name(data.user.username)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=f"call-channel-room-{call_channel.id}",
                room_admin=data.grants.room_admin,
                can_publish=data.grants.can_publish,
                can_subscribe=data.grants.can_subscribe,
                can_publish_data=data.grants.can_publish_data,
                can_publish_sources=[
                    str(item) for item in data.grants.can_publish_sources
                ],
                hidden=data.grants.hidden,
            )
        )
    ).to_jwt()

    return TokenResponseSchema(
        token=token,
        demo_url=str(
            URL(settings.livekit_demo_base_url).include_query_params(
                liveKitUrl=data.config.url, token=token
            )
        ),
    )
