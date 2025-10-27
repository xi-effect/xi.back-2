from collections.abc import AsyncIterator
from datetime import timezone
from uuid import UUID

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.utils import remove_none_values
from tests.notifications import factories

pytestmark = pytest.mark.anyio

RECIPIENT_NOTIFICATIONS_LIST_SIZE = 9


@pytest.fixture()
async def recipient_notifications(
    faker: Faker,
    active_session: ActiveSession,
    authorized_user_id: int,
) -> AsyncIterator[list[RecipientNotification]]:
    recipient_notifications: list[RecipientNotification] = []

    async with active_session():
        for i in range(RECIPIENT_NOTIFICATIONS_LIST_SIZE):
            notification: Notification = await Notification.create(
                payload=factories.NotificationSimpleInputFactory.build().payload,
            )
            recipient_notifications.append(
                await RecipientNotification.create(
                    notification=notification,
                    recipient_user_id=authorized_user_id,
                    read_at=(
                        None
                        if i % 3 == 0
                        else faker.date_time_between(tzinfo=timezone.utc)
                    ),
                )
            )

    recipient_notifications.sort(
        key=lambda recipient_notification: recipient_notification.notification.created_at,
        reverse=True,
    )

    yield recipient_notifications

    async with active_session():
        for recipient_notification in recipient_notifications:
            await recipient_notification.notification.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, RECIPIENT_NOTIFICATIONS_LIST_SIZE, id="start_to_end"),
        pytest.param(
            RECIPIENT_NOTIFICATIONS_LIST_SIZE // 2,
            RECIPIENT_NOTIFICATIONS_LIST_SIZE,
            id="middle_to_end",
        ),
        pytest.param(0, RECIPIENT_NOTIFICATIONS_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_notification_listing(
    authorized_client: TestClient,
    recipient_notifications: list[RecipientNotification],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current/notifications/searches/",
            json=remove_none_values(
                {
                    "cursor": (
                        None
                        if offset == 0
                        else {
                            "created_at": recipient_notifications[
                                offset - 1
                            ].notification.created_at.isoformat(),
                        }
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            RecipientNotification.ResponseSchema.model_validate(
                recipient_notification, from_attributes=True
            )
            for recipient_notification in recipient_notifications[offset:limit]
        ],
    )


@pytest.mark.parametrize(
    ("limit", "expected_count"),
    [
        pytest.param(
            RECIPIENT_NOTIFICATIONS_LIST_SIZE // 3 - 1,
            RECIPIENT_NOTIFICATIONS_LIST_SIZE // 3 - 1,
            id="limit_less_than_count",
        ),
        pytest.param(
            RECIPIENT_NOTIFICATIONS_LIST_SIZE,
            RECIPIENT_NOTIFICATIONS_LIST_SIZE // 3,
            id="limit_greater_than_count",
        ),
    ],
)
async def test_counting_unread_notifications(
    authorized_client: TestClient,
    recipient_notifications: list[RecipientNotification],
    limit: int,
    expected_count: int,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/unread-notifications-count/",
            params={"limit": limit},
        ),
        expected_json=expected_count,
    )


@freeze_time()
async def test_marking_notification_as_read(
    active_session: ActiveSession,
    authorized_client: TestClient,
    recipient_notification: RecipientNotification,
) -> None:
    assert_nodata_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current"
            f"/notifications/{recipient_notification.notification_id}/read/",
        ),
    )

    async with active_session() as session:
        session.add(recipient_notification)
        await session.refresh(recipient_notification)
        assert_contains(recipient_notification, {"read_at": datetime_utc_now()})


async def test_marking_notification_as_read_already_marked_as_read(
    faker: Faker,
    active_session: ActiveSession,
    authorized_client: TestClient,
    recipient_notification: RecipientNotification,
) -> None:
    async with active_session() as session:
        session.add(recipient_notification)
        await session.refresh(recipient_notification)
        recipient_notification.read_at = faker.past_datetime(tzinfo=timezone.utc)

    assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current"
            f"/notifications/{recipient_notification.notification_id}/read/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Notification already marked as read"},
    )


@pytest.mark.parametrize(
    "deleted_id",
    [
        pytest.param(
            lf("deleted_notification_id"),
            id="deleted_notification",
        ),
        pytest.param(
            lf("deleted_recipient_notification_id"),
            id="deleted_recipient_notification",
        ),
    ],
)
async def test_marking_notification_as_read_recipient_notification_not_found(
    authorized_client: TestClient,
    deleted_id: UUID,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current"
            f"/notifications/{deleted_id}/read/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Recipient notification not found"},
    )
