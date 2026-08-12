from httpx import Response
from pydantic import TypeAdapter
from starlette import status

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.generic_fluid_interface import Validator
from app.common.schemas.autocomplete_sch import SubjectSchema

subject_type_adapter = TypeAdapter(SubjectSchema)


class SubjectNotFoundException(Exception):
    pass


class SubjectNotFoundHandler(Validator[Response]):
    async def validate(self, data: Response) -> None:
        if (
            data.status_code == status.HTTP_404_NOT_FOUND
            and data.json()["detail"] == "Subject not found"
        ):
            raise SubjectNotFoundException


class AutocompleteBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/autocomplete-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def retrieve_subject(self, subject_id: int) -> SubjectSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(f"/subjects/{subject_id}/")
            )
            .validate(SubjectNotFoundHandler())
            .validate_status_code()
            .validate_json(subject_type_adapter)
        )
