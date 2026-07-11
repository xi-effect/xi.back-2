import random
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import Mock, call

import pytest
from faker import Faker
from pydantic_marshals.contains import UnorderedLiteralCollection, assert_contains
from respx import MockRouter

from app.common.config import settings
from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    ClassroomParticipantRecipientFilterSchema,
    NotificationInputV2Schema,
    SingleUserRecipientFilterSchema,
)
from app.notifications.services import recipients_svc
from tests.common.mock_stack import MockStack
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.utils import remove_none_values
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_iter_recipient_user_ids_from_single_user_filter() -> None:
    recipient_filter: SingleUserRecipientFilterSchema = (
        factories.SingleUserRecipientFilterFactory.build()
    )

    assert_contains(
        [
            recipient_user_id
            async for recipient_user_id in recipients_svc.iter_recipient_user_ids_from_filter(
                recipient_filter=recipient_filter
            )
        ],
        UnorderedLiteralCollection([recipient_filter.user_id]),
    )


@pytest.mark.parametrize(
    "role",
    [
        pytest.param(ClassroomRole.TUTOR, id="tutor"),
        pytest.param(ClassroomRole.STUDENT, id="student"),
        pytest.param(None, id="all"),
    ],
)
async def test_iter_recipient_user_ids_from_classroom_participant_filter(
    faker: Faker,
    classrooms_respx_mock: MockRouter,
    classroom_id: int,
    role: ClassroomRole | None,
) -> None:
    recipient_user_ids = random.sample(list(range(100)), k=faker.random_int(2, 5))

    classroom_bridge_mock = classrooms_respx_mock.get(
        path=f"/classrooms/{classroom_id}/participant-ids/",
        params=remove_none_values({"role": role}),
    ).respond(json=recipient_user_ids)

    recipient_filter = ClassroomParticipantRecipientFilterSchema(
        classroom_id=classroom_id,
        role=role,
    )

    assert_contains(
        [
            recipient_user_id
            async for recipient_user_id in recipients_svc.iter_recipient_user_ids_from_filter(
                recipient_filter=recipient_filter
            )
        ],
        UnorderedLiteralCollection(recipient_user_ids),
    )

    assert_last_httpx_request(
        classroom_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_generate_recipient_user_ids_for_v2_notification(
    faker: Faker,
    mock_stack: MockStack,
) -> None:
    recipient_user_ids = random.sample(list(range(100)), k=faker.random_int(2, 5))

    async def iter_recipient_user_ids(**_: Any) -> AsyncIterator[int]:
        for recipient_user_id in recipient_user_ids:
            yield recipient_user_id

    iter_recipient_user_ids_from_filter_mock = mock_stack.enter_mock(
        recipients_svc,
        "iter_recipient_user_ids_from_filter",
        mock=Mock(side_effect=iter_recipient_user_ids),
    )

    notification_data = NotificationInputV2Schema(
        payload=factories.NotificationSimpleInputFactory.build().payload,
        recipient_filters=[
            factories.SingleUserRecipientFilterFactory.build(),
            factories.ClassroomParticipantRecipientFilterFactory.build(),
        ],
    )

    assert_contains(
        await recipients_svc.generate_recipient_user_ids_for_notification(
            notification_data=notification_data
        ),
        UnorderedLiteralCollection(recipient_user_ids),
    )

    iter_recipient_user_ids_from_filter_mock.assert_has_calls(
        [
            call(recipient_filter=recipient_filter)
            for recipient_filter in notification_data.recipient_filters
        ]
    )
