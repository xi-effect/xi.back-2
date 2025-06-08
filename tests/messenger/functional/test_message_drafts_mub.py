from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.messenger.models.chats_db import Chat
from app.messenger.models.message_drafts_db import MessageDraft
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.messenger.factories import (
    MessageDraftInputMUBFactory,
    MessageDraftPatchMUBFactory,
)

pytestmark = pytest.mark.anyio


async def test_message_draft_creating(
    active_session: ActiveSession,
    mub_client: TestClient,
    chat: Chat,
    sender_user_id: int,
) -> None:
    input_data = MessageDraftInputMUBFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/messenger-service/chats/{chat.id}/users/{sender_user_id}/draft/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **input_data,
            "chat_id": chat.id,
            "user_id": sender_user_id,
        },
    )

    async with active_session():
        message_draft = await MessageDraft.find_first_by_kwargs(
            chat_id=chat.id, user_id=sender_user_id
        )
        assert message_draft is not None
        await message_draft.delete()


async def test_message_draft_creating_chat_not_found(
    mub_client: TestClient,
    deleted_chat_id: int,
    sender_user_id: int,
) -> None:
    input_data = MessageDraftInputMUBFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/messenger-service/chats/{deleted_chat_id}/users/{sender_user_id}/draft/",
            json=input_data,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Chat not found"},
    )


async def test_message_draft_retrieving(
    mub_client: TestClient,
    message_draft: MessageDraft,
    message_draft_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/messenger-service/chats/{message_draft.chat_id}/users/{message_draft.user_id}/draft/",
        ),
        expected_json=message_draft_data,
    )


async def test_message_draft_updating(
    mub_client: TestClient, message_draft: MessageDraft, message_draft_data: AnyJSON
) -> None:
    message_draft_patch_data = MessageDraftPatchMUBFactory.build_json()
    assert_response(
        mub_client.patch(
            f"/mub/messenger-service/chats/{message_draft.chat_id}/users/{message_draft.user_id}/draft/",
            json=message_draft_patch_data,
        ),
        expected_json=message_draft_data | message_draft_patch_data,
    )


async def test_message_draft_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    message_draft: MessageDraft,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/messenger-service/chats/{message_draft.chat_id}/users/{message_draft.user_id}/draft/"
        ),
    )

    async with active_session():
        assert (
            await MessageDraft.find_first_by_kwargs(
                chat_id=message_draft.chat_id, user_id=message_draft.user_id
            )
        ) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PATCH", MessageDraftPatchMUBFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_message_draft_not_finding(
    mub_client: TestClient,
    deleted_message_draft: MessageDraft,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/messenger-service/chats/{deleted_message_draft.chat_id}/users/{deleted_message_draft.user_id}/draft/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Message draft not found"},
    )
