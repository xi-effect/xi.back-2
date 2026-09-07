import json
from collections.abc import Iterator
from typing import Any
from urllib.parse import parse_qs

import pytest
from httpx import Request
from pydantic_marshals.contains import TypeChecker, assert_contains
from respx import MockRouter, Route, mock

from app.common.config import settings


@pytest.fixture()
def autocomplete_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(
        base_url=f"{settings.bridge_base_url}/internal/autocomplete-service"
    )
    with mock_router:
        yield mock_router


@pytest.fixture()
def classrooms_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(
        base_url=f"{settings.bridge_base_url}/internal/classroom-service"
    )
    with mock_router:
        yield mock_router


@pytest.fixture()
def notifications_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(
        base_url=f"{settings.bridge_base_url}/internal/notification-service"
    )
    with mock_router:
        yield mock_router


@pytest.fixture()
def users_internal_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(
        base_url=f"{settings.bridge_base_url}/internal/user-service"
    )
    with mock_router:
        yield mock_router


@pytest.fixture()
def users_public_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(
        base_url=f"{settings.bridge_base_url}/api/public/user-service"
    )
    with mock_router:
        yield mock_router


@pytest.fixture()
def vk_respx_mock() -> Iterator[MockRouter]:
    mock_router: MockRouter = mock(base_url=settings.vk_server_base_url)
    with mock_router:
        yield mock_router


def assert_last_httpx_request(
    mock_route: Route,
    *,
    expected_headers: dict[str, TypeChecker] | None = None,
    expected_method: TypeChecker | None = None,
    expected_path: TypeChecker | None = None,
    expected_params: TypeChecker | None = None,
    expected_data: dict[str, TypeChecker] | None = None,
    expected_json: TypeChecker | None = None,
) -> None:
    assert mock_route.call_count == 1
    last_request: Request = mock_route.calls.last.request

    real: dict[str, Any] = {}
    expected: dict[str, Any] = {"json": expected_json}

    if expected_headers is not None:
        real["headers"] = last_request.headers
        expected["headers"] = expected_headers

    if expected_method is not None:
        real["method"] = last_request.method
        expected["method"] = expected_method

    if expected_path is not None:
        real["path"] = last_request.url.path
        expected["path"] = expected_path

    if expected_params is not None:
        real["params"] = dict(last_request.url.params)
        expected["params"] = expected_params

    if expected_data is not None:
        real["data"] = parse_qs(last_request.content.decode())
        expected["data"] = expected_data

    try:
        real["json"] = json.loads(last_request.content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        real["json"] = None

    assert_contains(real, expected)
