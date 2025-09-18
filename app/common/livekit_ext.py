from collections.abc import Iterator
from types import TracebackType
from typing import Self

from livekit.api import AccessToken, LiveKitAPI, VideoGrants
from livekit.api.room_service import RoomService
from livekit.protocol.models import ParticipantInfo, Room
from livekit.protocol.room import (
    CreateRoomRequest,
    ListParticipantsRequest,
    ListRoomsRequest,
)


class LiveKit:
    def __init__(self, url: str, api_key: str, api_secret: str) -> None:
        self.url = url
        self.api_key = api_key
        self.api_secret = api_secret
        self._api: LiveKitAPI | None = None

    async def __aenter__(self) -> Self:
        self._api = LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        await self._api.__aenter__()  # type: ignore[no-untyped-call]  # lib's fault
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.api.__aexit__(  # type: ignore[no-untyped-call]  # lib's fault
            exc_type=exc_type,
            exc_val=exc_val,
            exc_tb=exc_tb,
        )

    @property
    def api(self) -> LiveKitAPI:
        if self._api is None:
            raise EnvironmentError("Livekit is not initialized")
        return self._api

    @property
    def room(self) -> RoomService:
        return self.api.room

    def generate_access_token(self, identity: str, name: str, room_name: str) -> str:
        return (
            AccessToken(self.api_key, self.api_secret)
            .with_identity(identity=identity)
            .with_name(name=name)
            .with_grants(VideoGrants(room_join=True, room=room_name))
        ).to_jwt()

    async def list_rooms(self, room_names: list[str]) -> Iterator[Room]:
        response = await self.room.list_rooms(ListRoomsRequest(names=room_names))
        return (room for room in response.rooms)

    async def find_or_create_room(self, room_name: str) -> Room:
        return await self.room.create_room(CreateRoomRequest(name=room_name))

    async def list_room_participants(self, room_name: str) -> Iterator[ParticipantInfo]:
        response = await self.room.list_participants(
            ListParticipantsRequest(room=room_name)
        )
        return (participant for participant in response.participants)
