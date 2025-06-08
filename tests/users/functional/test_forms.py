from typing import BinaryIO
from unittest.mock import Mock

import pytest
from discord_webhook import AsyncDiscordWebhook  # type: ignore[import-untyped]
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.users import factories

pytestmark = pytest.mark.anyio


async def test_demo_form_submitting(
    mock_stack: MockStack,
    client: TestClient,
) -> None:
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    execute_mock = mock_stack.enter_async_mock(
        AsyncDiscordWebhook, "execute", return_value=response_mock
    )
    mock_stack.enter_mock(
        "app.users.routes.forms_rst.settings.demo_webhook_url", return_value=""
    )

    assert_nodata_response(
        client.post(
            "/api/public/user-service/demo-applications/",
            json=factories.DemoFormFactory.build_json(),
        )
    )
    execute_mock.assert_called_once()
    response_mock.raise_for_status.assert_called_once()


async def test_demo_form_submitting_missing_webhook_url(client: TestClient) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/demo-applications/",
            json=factories.DemoFormFactory.build_json(),
        ),
        expected_code=500,
        expected_json={"detail": "Webhook url is not set"},
    )


async def test_vacancy_form_submitting(
    mock_stack: MockStack,
    client: TestClient,
    pdf_data: tuple[str, BinaryIO, str],
    vacancy_form_data: AnyJSON,
) -> None:
    response_mock = Mock()
    response_mock.raise_for_status = Mock()
    execute_mock = mock_stack.enter_async_mock(
        AsyncDiscordWebhook, "execute", return_value=response_mock
    )
    mock_stack.enter_mock(
        "app.users.routes.forms_rst.settings.vacancy_webhook_url", return_value=""
    )

    assert_nodata_response(
        client.post(
            "/api/public/user-service/v2/vacancy-applications/",
            data=vacancy_form_data,
            files={"resume": pdf_data},
        )
    )
    execute_mock.assert_called_once()
    response_mock.raise_for_status.assert_called_once()


async def test_vacancy_form_submitting_invalid_file_format(
    faker: Faker,
    client: TestClient,
    vacancy_form_data: AnyJSON,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/v2/vacancy-applications/",
            data=vacancy_form_data,
            files={
                "resume": ("resume.pdf", faker.random.randbytes(100), "application/pdf")
            },
        ),
        expected_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_json={"detail": "Invalid file format"},
    )


async def test_vacancy_form_submitting_missing_webhook_url(
    client: TestClient,
    pdf_data: tuple[str, BinaryIO, str],
    vacancy_form_data: AnyJSON,
) -> None:
    assert_response(
        client.post(
            "/api/public/user-service/v2/vacancy-applications/",
            data=vacancy_form_data,
            files={"resume": pdf_data},
        ),
        expected_code=500,
        expected_json={"detail": "Webhook url is not set"},
    )
