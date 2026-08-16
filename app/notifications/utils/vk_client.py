from __future__ import annotations

from typing import ClassVar

from httpx import AsyncClient
from pydantic import TypeAdapter

from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.generic_fluid_interface import PipelineBuilder, Transformer
from app.notifications.schemas.vk.vk_base_sch import (
    ErrorSchema,
    MethodName,
    ResponseWrapperSchema,
)
from app.notifications.schemas.vk.vk_messages_sch import (
    MessageSendInputSchema,
    send_message_response_type_adapter,
)
from app.notifications.schemas.vk.vk_users_sch import (
    UserFieldName,
    UserResponseSchema,
    UsersGetInputSchema,
    users_get_response_type_adapter,
)


class VKResponseWithErrorException(Exception):
    def __init__(self, error: ErrorSchema) -> None:
        self.error = error


class VKResponseWithoutResponseException(Exception):
    pass


class VKResponseUnwrapper[R](Transformer[ResponseWrapperSchema[R], R]):
    async def transform(self, data: ResponseWrapperSchema[R]) -> R:
        if data.error is not None:
            raise VKResponseWithErrorException(data.error)
        if data.response is None:
            raise VKResponseWithoutResponseException
        return data.response


class VKWrappedJSONPipelineBuilder[ResponseSchema](
    PipelineBuilder[ResponseWrapperSchema[ResponseSchema]]
):
    def validate_success_and_unwrap(self) -> PipelineBuilder[ResponseSchema]:
        return self.transform(VKResponseUnwrapper())


class VKResponsePipelineBuilder(ResponsePipelineBuilder):
    def validate_wrapper[ResponseSchema](
        self, type_adapter: TypeAdapter[ResponseWrapperSchema[ResponseSchema]]
    ) -> VKWrappedJSONPipelineBuilder[ResponseSchema]:
        return self.validate_json(type_adapter).swap_builder_type(
            VKWrappedJSONPipelineBuilder
        )


class VKClient(AsyncClient):
    api_version: ClassVar[str] = "5.199"

    def __init__(self, base_url: str, api_token: str, group_id: int) -> None:
        self.api_token = api_token
        self.group_id = group_id

        super().__init__(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.api_token}"},
            params={"group_id": self.group_id, "v": self.api_version},
        )

    async def send_message(
        self,
        data: MessageSendInputSchema,
    ) -> int:
        return (
            await VKResponsePipelineBuilder.initialize_from_request(
                self.post(
                    MethodName.MESSAGES__SEND,
                    data=data.model_dump(mode="json"),
                )
            )
            .validate_status_code()
            .validate_wrapper(send_message_response_type_adapter)
            .validate_success_and_unwrap()
        )

    async def get_user(
        self,
        user_id: int,
    ) -> UserResponseSchema | None:
        users_data = (
            await VKResponsePipelineBuilder.initialize_from_request(
                self.post(
                    MethodName.USERS__GET,
                    data=UsersGetInputSchema(
                        user_ids=[user_id],
                        fields=[UserFieldName.SCREEN_NAME],
                    ).model_dump(mode="json"),
                )
            )
            .validate_status_code()
            .validate_wrapper(users_get_response_type_adapter)
            .validate_success_and_unwrap()
        )
        return next(iter(users_data), None)
