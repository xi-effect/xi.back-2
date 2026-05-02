from httpx import Response
from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_external_json_response
from app.common.config import settings


class ClassroomsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/classroom-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_external_json_response(TypeAdapter(list[int]))
    async def list_classroom_student_ids(self, classroom_id: int) -> Response:
        return await self.client.get(
            f"/classrooms/{classroom_id}/students/",
        )

    @validate_external_json_response(TypeAdapter(list[int]))
    async def list_tutor_classroom_ids(self, tutor_id: int) -> Response:
        return await self.client.get(
            f"/tutors/{tutor_id}/classroom-ids/",
        )

    @validate_external_json_response(TypeAdapter(list[int]))
    async def list_student_classroom_ids(self, student_id: int) -> Response:
        return await self.client.get(
            f"/students/{student_id}/classroom-ids/",
        )
