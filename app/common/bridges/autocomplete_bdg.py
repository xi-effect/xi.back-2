from httpx import AsyncClient
from pydantic import TypeAdapter
from starlette import status

from app.common.config import settings
from app.common.schemas.autocomplete_sch import SubjectSchema


class AutocompleteBridge:
    def __init__(self) -> None:
        self.client = AsyncClient(
            base_url=f"{settings.bridge_base_url}/internal/autocomplete-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def retrieve_subject(self, subject_id: int) -> SubjectSchema | None:
        response = await self.client.get(f"/subjects/{subject_id}/")
        if (
            response.status_code == status.HTTP_404_NOT_FOUND
            and response.json()["detail"] == "Subject not found"
        ):
            return None
        response.raise_for_status()
        return TypeAdapter(SubjectSchema).validate_python(response.json())
