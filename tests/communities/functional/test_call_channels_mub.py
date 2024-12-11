import pytest
from jwt import decode
from jwt.exceptions import PyJWTError
from pydantic import HttpUrl
from pydantic_marshals.contains import assert_contains
from starlette.datastructures import URL, QueryParams
from starlette.testclient import TestClient

from app.common.config import settings
from app.communities.models.call_channels_db import CallChannel
from tests.common.assert_contains_ext import assert_response
from tests.communities.factories import TokenRequestSchemaFactory

pytestmark = pytest.mark.anyio


async def test_call_channel_livekit_token_generating(
    mub_client: TestClient,
    call_channel: CallChannel,
) -> None:
    token_input_data = TokenRequestSchemaFactory.build()
    response_json = assert_response(
        mub_client.post(
            f"/mub/community-service/channels/{call_channel.id}/call/tokens/",
            json=token_input_data.model_dump(mode="json", by_alias=True),
        ),
        expected_json={"token": str, "demo_url": HttpUrl},
    ).json()

    try:
        decoded_token = decode(
            response_json["token"],
            token_input_data.config.api_secret,
            algorithms=["HS256"],
        )
    except PyJWTError as e:
        pytest.fail(f"Token decoding failed {e}")

    assert_contains(
        decoded_token,
        {
            "sub": str(token_input_data.user.user_id),
            "name": token_input_data.user.username,
            "iss": token_input_data.config.api_key,
            "video": {
                "roomJoin": True,
                "room": f"call-channel-room-{call_channel.id}",
                "roomAdmin": token_input_data.grants.room_admin,
                "canPublish": token_input_data.grants.can_publish,
                "canSubscribe": token_input_data.grants.can_subscribe,
                "canPublishData": token_input_data.grants.can_publish_data,
                "canPublishSources": token_input_data.grants.can_publish_sources,
                "hidden": token_input_data.grants.hidden,
            },
        },
    )

    real_demo_url = URL(response_json["demo_url"])
    expected_demo_url = URL(settings.livekit_demo_base_url).include_query_params(
        token=response_json["token"], liveKitUrl=token_input_data.config.url
    )

    assert_contains(
        {
            "scheme": real_demo_url.scheme,
            "netloc": real_demo_url.netloc,
            "path": real_demo_url.path,
            "query_params": dict(QueryParams(real_demo_url.query)),
        },
        {
            "scheme": expected_demo_url.scheme,
            "netloc": expected_demo_url.netloc,
            "path": expected_demo_url.path,
            "query_params": dict(QueryParams(expected_demo_url.query)),
        },
    )


async def test_call_channel_livekit_token_generating_call_channel_not_found(
    mub_client: TestClient,
    deleted_call_channel_id: int,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/community-service/channels/{deleted_call_channel_id}/call/tokens/"
        ),
        expected_code=404,
        expected_json={"detail": "Call-channel not found"},
    )
