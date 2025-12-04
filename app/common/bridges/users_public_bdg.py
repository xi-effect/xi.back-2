from typing import BinaryIO

from httpx import Response

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import validate_external_json_response
from app.common.config import settings
from app.common.schemas.vacancy_form_sch import VacancyFormSchema


class UsersPublicBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/api/public/user-service",
        )

    @validate_external_json_response()
    async def apply_for_vacancy(
        self,
        vacancy_form: VacancyFormSchema,
        resume: tuple[str, BinaryIO, str],
    ) -> Response:
        return await self.client.post(
            "/v2/vacancy-applications/",
            data=vacancy_form.model_dump(),
            files={"resume": resume},
        )
