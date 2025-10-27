from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from typing import Any, Protocol, cast
from unittest.mock import patch

from engineio import async_socket, packet as eio_packet  # type: ignore[import-untyped]
from pydantic_marshals.contains import TypeChecker, assert_contains
from socketio import packet as sio_packet  # type: ignore[import-untyped]
from starlette import status
from tmexio import TMEXIO
from tmexio.types import DataType

from app.common.dependencies.authorization_dep import (
    AUTH_SESSION_ID_HEADER_NAME,
    AUTH_USER_ID_HEADER_NAME,
    AUTH_USERNAME_HEADER_NAME,
    ProxyAuthData,
)
from app.common.dependencies.authorization_sio_dep import header_to_wsgi_var

SessionIDType = str


@dataclass()
class TMEXIOEvent:
    name: str
    data: Any


class TMEXIOTestClient:
    def __init__(self, tmexio: TMEXIO, eio_sid: SessionIDType) -> None:
        self.tmexio = tmexio
        self.eio_sid: SessionIDType = eio_sid
        self._sio_sid: SessionIDType | None = None

        self.eio_packets: list[eio_packet.Packet] = []
        self.sio_packets: list[sio_packet.Packet] = []

        self.events: list[TMEXIOEvent] = []
        self.event_iterator: Iterator[TMEXIOEvent] = iter(self.events)

    @property
    def sio_sid(self) -> SessionIDType:
        if self._sio_sid is None:
            raise ConnectionError("SocketIO is not connected")
        return self._sio_sid

    def handle_sio_message(self, sio_pkt: sio_packet.Packet) -> None:
        self.sio_packets.append(sio_pkt)

        # socketio handling: `socketio.async_client.AsyncClient._handle_eio_message`
        # connected to eio via: `socketio.base_client.eio.on("message", ...)`
        match sio_pkt.packet_type:
            case sio_packet.CONNECT:
                self._sio_sid = sio_pkt.data["sid"]
            case sio_packet.CONNECT_ERROR:
                self._sio_sid = None
                pass  # TODO
            case sio_packet.EVENT:
                # save instead of calling `socketio.async_client.AsyncClient._handle_event`
                self.events.append(
                    TMEXIOEvent(name=sio_pkt.data[0], data=sio_pkt.data[1])
                )
            case sio_packet.DISCONNECT:
                self._sio_sid = None
            case _:
                raise RuntimeError(
                    f"Unhandled SIO packet ({sio_pkt.packet_type}): {sio_pkt.data}"
                )

    def handle_eio_message(self, eio_pkt: eio_packet.Packet) -> None:
        self.eio_packets.append(eio_pkt)

        # engineio handling: `engineio.async_client.AsyncClient._receive_packet`
        match eio_pkt.packet_type:
            case eio_packet.NOOP | eio_packet.PING | eio_packet.PONG:
                pass  # we ignore these in test client
            case eio_packet.MESSAGE:
                sio_pkt = sio_packet.Packet(encoded_packet=eio_pkt.data)
                self.handle_sio_message(sio_pkt=sio_pkt)
            case _:  # OPEN & CLOSE are not handled, since we avoid connecting for real
                raise RuntimeError(
                    f"Unhandled EIO packet ({eio_pkt.packet_type}): {eio_pkt.data}"
                )

    async def raw_emit(self, event_name: str, *data: Any) -> Any:
        # Where to look if this needs to go deeper:
        # `engineio.async_socket.AsyncSocket._websocket_handler`
        # `engineio.async_socket.AsyncSocket.receive`
        # `engineio.async_server.AsyncServer._trigger_event`
        # `socketio.base_server.eio.on("message", ...)`
        # `socketio.async_server.AsyncServer._handle_eio_message`
        # `socketio.async_server.AsyncServer._handle_event`
        # `socketio.async_server.AsyncServer._trigger_event`
        return await self.tmexio.server.backend._trigger_event(
            event_name, "/", self.sio_sid, *data
        )

    async def emit(self, event_name: str, **kwargs: Any) -> tuple[int, DataType]:
        # TMEXIO-typed version (doesn't actually check types, just assumes them)
        args = (kwargs,) if kwargs else ()
        return cast(tuple[int, DataType], await self.raw_emit(event_name, *args))

    def _current_rooms(self) -> Iterator[str]:
        for room_name in self.tmexio.server.rooms(self.sio_sid, namespace="/"):
            if room_name == self.sio_sid:
                continue
            yield room_name

    def current_rooms(self) -> set[str]:
        return set(self._current_rooms())

    async def enter_room(self, room_name: str) -> None:
        await self.tmexio.server.enter_room(self.sio_sid, room_name)

    async def leave_room(self, room_name: str) -> None:
        await self.tmexio.server.leave_room(self.sio_sid, room_name)

    async def clear_rooms(self) -> None:
        for room_name in self._current_rooms():
            await self.leave_room(room_name=room_name)

    def assert_rooms(self, required_rooms: str) -> None:  # TODO
        pass

    def reset_event_iteration(self) -> None:
        self.event_iterator = iter(self.events)

    def assert_next_event(
        self,
        expected_name: str,
        expected_data: TypeChecker,
    ) -> TMEXIOEvent:
        event = next(self.event_iterator, None)
        if event is None:
            raise AssertionError("Next event not found")

        assert_contains(
            {"name": event.name, "data": event.data},
            {"name": expected_name, "data": expected_data},
        )

        return event

    def assert_no_more_events(self) -> None:
        assert list(self.event_iterator) == []


class TMEXIOTestServer:
    def __init__(self, tmexio: TMEXIO) -> None:
        self.tmexio = tmexio
        self.backend = tmexio.server.backend

        self.clients: dict[SessionIDType, TMEXIOTestClient] = {}

    async def _send_packet(
        self, eio_sid: SessionIDType, eio_pkt: eio_packet.Packet
    ) -> None:
        client = self.clients.get(eio_sid)
        if client is None:
            raise ConnectionError(f"Client {eio_sid} is not connected")
        client.handle_eio_message(eio_pkt)

    def create_mock(self) -> Any:
        return patch.object(self.backend.eio, "send_packet", self._send_packet)

    @asynccontextmanager
    async def client(
        self, data: Any = None, environ: dict[str, str] | None = None
    ) -> AsyncIterator[TMEXIOTestClient]:
        eio_sid: SessionIDType = self.backend.eio.generate_id()
        self.backend.eio.sockets[eio_sid] = async_socket.AsyncSocket(
            self.backend.eio, eio_sid
        )

        client = TMEXIOTestClient(tmexio=self.tmexio, eio_sid=eio_sid)
        self.clients[eio_sid] = client

        await self.backend._handle_eio_connect(eio_sid=eio_sid, environ=environ or {})
        await self.backend._handle_connect(
            eio_sid=eio_sid,
            namespace="/",
            data=data,  # TODO support multiple namespaces
        )

        # TODO check client.packets for the CONNECT-type packet

        yield client

        await self.backend._handle_disconnect(eio_sid=eio_sid, namespace="/")
        await self.backend._handle_eio_disconnect(eio_sid=eio_sid)

        # TODO check client.packets for the DISCONNECT-type packet

    @asynccontextmanager
    async def listener(
        self,
        room_name: str | None = None,
        data: Any = None,
        environ: dict[str, str] | None = None,
    ) -> AsyncIterator[TMEXIOTestClient]:
        async with self.client(data=data, environ=environ) as client:
            await client.clear_rooms()
            if room_name is not None:
                await client.enter_room(room_name=room_name)
            yield client

    def authorized_client(  # xieffect specific
        self, proxy_auth_data: ProxyAuthData
    ) -> AbstractAsyncContextManager[TMEXIOTestClient]:
        return self.client(environ=proxy_auth_data_to_sio_environ(proxy_auth_data))

    def authorized_listener(  # xieffect specific
        self, proxy_auth_data: ProxyAuthData, room_name: str | None = None
    ) -> AbstractAsyncContextManager[TMEXIOTestClient]:
        return self.listener(
            room_name=room_name, environ=proxy_auth_data_to_sio_environ(proxy_auth_data)
        )


class TMEXIOListenerFactory(Protocol):
    async def __call__(self, room_name: str | None = None) -> TMEXIOTestClient:
        pass


def assert_ack(
    real_ack: tuple[int, Any],
    expected_code: int = status.HTTP_200_OK,
    expected_data: TypeChecker = None,
) -> tuple[int, Any]:
    assert_contains(
        {"code": real_ack[0], "data": real_ack[1]},
        {"code": expected_code, "data": expected_data},
    )
    return real_ack


def proxy_auth_data_to_sio_environ(proxy_auth_data: ProxyAuthData) -> dict[str, str]:
    return {
        header_to_wsgi_var(AUTH_SESSION_ID_HEADER_NAME): str(
            proxy_auth_data.session_id
        ),
        header_to_wsgi_var(AUTH_USER_ID_HEADER_NAME): str(proxy_auth_data.user_id),
        header_to_wsgi_var(AUTH_USERNAME_HEADER_NAME): proxy_auth_data.username,
    }
