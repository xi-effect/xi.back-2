from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.classrooms_sch import ClassroomRole

integer_list_type_adapter = TypeAdapter(list[int])


class ClassroomsBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/classroom-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def list_classroom_participant_ids(
        self,
        classroom_id: int,
        role: ClassroomRole | None = None,
    ) -> list[int]:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    f"/classrooms/{classroom_id}/participant-ids/",
                    params=None if role is None else {"role": role},
                )
            )
            .validate_status_code()
            .validate_json(integer_list_type_adapter)
        )

    async def list_tutor_classroom_ids(self, tutor_id: int) -> list[int]:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    f"/tutors/{tutor_id}/classroom-ids/",
                )
            )
            .validate_status_code()
            .validate_json(integer_list_type_adapter)
        )

    async def list_student_classroom_ids(self, student_id: int) -> list[int]:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    f"/students/{student_id}/classroom-ids/",
                )
            )
            .validate_status_code()
            .validate_json(integer_list_type_adapter)
        )
