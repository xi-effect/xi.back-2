import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from respx import MockRouter

from app.common.config import VKBotSettings
from app.notifications.config import vk_app
from app.notifications.schemas.vk.vk_messages_sch import MessageSendInputSchema
from app.notifications.utils.vk_client import (
    VKResponseWithErrorException,
    VKResponseWithoutResponseException,
)
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_message_sending_error_response(
    faker: Faker,
    vk_respx_mock: MockRouter,
    vk_notifications_bot_settings: VKBotSettings,
    vk_peer_id: int,
) -> None:
    expected_error_data: AnyJSON = factories.ErrorFactory.build_json()
    message_text: str = faker.sentence()

    vk_send_message_mock = vk_respx_mock.post(path="/messages.send").respond(
        json={"error": expected_error_data}
    )

    with pytest.raises(VKResponseWithErrorException) as exc_info:
        await vk_app.client.send_message(
            data=MessageSendInputSchema(
                peer_id=vk_peer_id,
                message=message_text,
            )
        )

    assert_contains(exc_info, {"value": {"error": expected_error_data}})

    assert_last_httpx_request(
        vk_send_message_mock,
        expected_headers={
            "Authorization": f"Bearer {vk_notifications_bot_settings.api_token}"
        },
        expected_data={
            "peer_id": [str(vk_peer_id)],
            "message": [message_text],
        },
    )


async def test_message_sending_empty_response(
    faker: Faker,
    vk_respx_mock: MockRouter,
    vk_notifications_bot_settings: VKBotSettings,
    vk_peer_id: int,
) -> None:
    message_text: str = faker.sentence()

    vk_send_message_mock = vk_respx_mock.post(path="/messages.send").respond(json={})

    with pytest.raises(VKResponseWithoutResponseException):
        await vk_app.client.send_message(
            data=MessageSendInputSchema(
                peer_id=vk_peer_id,
                message=message_text,
            )
        )

    assert_last_httpx_request(
        vk_send_message_mock,
        expected_headers={
            "Authorization": f"Bearer {vk_notifications_bot_settings.api_token}"
        },
        expected_data={
            "peer_id": [str(vk_peer_id)],
            "message": [message_text],
        },
    )
