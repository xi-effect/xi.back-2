from httpx import AsyncClient, Response
from pydantic import TypeAdapter

from app.common.bridges.utils import validate_json_response
from app.common.config import settings


class ClassroomsBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/classroom-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_json_response(TypeAdapter(list[int]))
    async def list_classroom_student_ids(self, classroom_id: int) -> Response:
        return await self.client.get(
            f"/classrooms/{classroom_id}/students/",
        )
