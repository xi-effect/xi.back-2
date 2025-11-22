from httpx import Response
from pydantic import TypeAdapter
from starlette import status

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_external_json_response
from app.common.config import settings
from app.common.schemas.autocomplete_sch import SubjectSchema


class SubjectNotFoundException(Exception):
    pass


class AutocompleteBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/autocomplete-service",
            headers={"X-Api-Key": settings.api_key},
        )

    @validate_external_json_response(TypeAdapter(SubjectSchema))
    async def retrieve_subject(self, subject_id: int) -> Response:
        response = await self.client.get(f"/subjects/{subject_id}/")
        if (
            response.status_code == status.HTTP_404_NOT_FOUND
            and response.json()["detail"] == "Subject not found"
        ):
            raise SubjectNotFoundException
        return response
