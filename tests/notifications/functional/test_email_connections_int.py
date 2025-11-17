import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.notifications.models.email_connections_db import EmailConnection
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_email_connection_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    authorized_user_id: int,
) -> None:
    input_data = factories.EmailConnectionInputFactory.build_json()

    assert_nodata_response(
        internal_client.put(
            "/internal/notification-service"
            f"/users/{authorized_user_id}/email-connection/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
    )

    async with active_session():
        email_connection = await EmailConnection.find_first_by_id(authorized_user_id)
        assert email_connection is not None
        assert_contains(email_connection, input_data)
        await email_connection.delete()


async def test_email_connection_updating(
    active_session: ActiveSession,
    internal_client: TestClient,
    email_connection: EmailConnection,
) -> None:
    input_data = factories.EmailConnectionInputFactory.build_json()

    assert_nodata_response(
        internal_client.put(
            "/internal/notification-service"
            f"/users/{email_connection.user_id}/email-connection/",
            json=input_data,
        ),
    )

    async with active_session() as session:
        session.add(email_connection)
        await session.refresh(email_connection)
        assert_contains(email_connection, input_data)
