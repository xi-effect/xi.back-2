from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.messenger.models.chat_users_db import ChatUser
from app.messenger.models.chats_db import Chat
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.messenger.factories import ChatUserInputFactory, ChatUserPatchFactory

pytestmark = pytest.mark.anyio


async def test_chat_user_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    chat: Chat,
    sender_user_id: int,
) -> None:
    chat_user_input_data = ChatUserInputFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/messenger-service/chats/{chat.id}/users/{sender_user_id}/",
            json=chat_user_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **chat_user_input_data,
            "chat_id": chat.id,
            "user_id": sender_user_id,
        },
    )

    async with active_session():
        chat_user = await ChatUser.find_first_by_kwargs(
            chat_id=chat.id, user_id=sender_user_id
        )
        assert chat_user is not None
        await chat_user.delete()


async def test_chat_user_creation_chat_not_found(
    mub_client: TestClient,
    deleted_chat_id: int,
    sender_user_id: int,
) -> None:
    chat_user_input_data = ChatUserInputFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/messenger-service/chats/{deleted_chat_id}/users/{sender_user_id}/",
            json=chat_user_input_data,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Chat not found"},
    )


async def test_chat_user_retrieving(
    mub_client: TestClient,
    chat_user: ChatUser,
    chat_user_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{chat_user.chat_id}/users/{chat_user.user_id}/"
        ),
        expected_json=chat_user_data,
    )


async def test_chat_user_updating(
    mub_client: TestClient,
    chat_user: ChatUser,
    chat_user_data: AnyJSON,
) -> None:
    chat_user_patch_data = ChatUserPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/messenger-service/chats/{chat_user.chat_id}/users/{chat_user.user_id}/",
            json=chat_user_patch_data,
        ),
        expected_json={**chat_user_data, **chat_user_patch_data},
    )


async def test_chat_user_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    chat_user: ChatUser,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/messenger-service/chats/{chat_user.chat_id}/users/{chat_user.user_id}/"
        ),
    )

    async with active_session():
        assert (
            await ChatUser.find_first_by_kwargs(
                chat_id=chat_user.chat_id, user_id=chat_user.user_id
            )
        ) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", ChatUserPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_chat_user_not_finding(
    mub_client: TestClient,
    deleted_chat_user: ChatUser,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/messenger-service/chats/{deleted_chat_user.chat_id}/users/{deleted_chat_user.user_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Chat-user not found"},
    )
