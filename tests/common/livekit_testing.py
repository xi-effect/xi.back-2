from typing import Any
from unittest.mock import AsyncMock

import pytest
from google.protobuf.message import Message
from livekit.api.twirp_client import TwirpClient

from tests.common.mock_stack import MockStack


class LiveKitRouteMock:
    def __init__(self, response_data: Message) -> None:
        self.request_data: Message | None = None
        self.response_data = response_data

    def request(
        self,
        request_data: Message,
        response_class: type[Message],
    ) -> Message:
        assert self.request_data is None, "LiveKit mock has been called before"
        assert isinstance(self.response_data, response_class)
        self.request_data = request_data
        return self.response_data

    def assert_requested_once_with(self, expected_data: Message) -> None:
        assert self.request_data is not None, "LiveKit mock was never requested"
        assert self.request_data == expected_data


class LiveKitMock:
    def __init__(self) -> None:
        self.route_mocks: dict[tuple[str, str], LiveKitRouteMock] = {}

    def route(
        self, service: str, method: str, response_data: Message
    ) -> LiveKitRouteMock:
        route_mock = LiveKitRouteMock(response_data)
        self.route_mocks[(service, method)] = route_mock
        return route_mock

    async def handle(
        self,
        service: str,
        method: str,
        data: Message,
        _headers: dict[str, str],
        response_class: type[Message],
        **_kwargs: Any,
    ) -> Message:
        route_mock = self.route_mocks.get((service, method))
        assert (
            route_mock is not None
        ), f"Livekit endpoint {service} {method} is not mocked"
        return route_mock.request(request_data=data, response_class=response_class)


@pytest.fixture()
async def livekit_mock(mock_stack: MockStack) -> LiveKitMock:
    livekit_mock = LiveKitMock()
    mock_stack.enter_async_mock(
        TwirpClient, "request", mock=AsyncMock(side_effect=livekit_mock.handle)
    )
    return livekit_mock
