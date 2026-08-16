from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.users_sch import UserProfileSchema

user_profile_type_adapter = TypeAdapter(UserProfileSchema)
user_id_to_user_profile_dict_type_adapter = TypeAdapter(dict[int, UserProfileSchema])


class UsersInternalBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/user-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def retrieve_multiple_users(
        self, user_ids: list[int]
    ) -> dict[int, UserProfileSchema]:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    "/users/",
                    params={"user_ids": user_ids},
                )
            )
            .validate_status_code()
            .validate_json(user_id_to_user_profile_dict_type_adapter)
        )

    async def retrieve_user(self, user_id: int) -> UserProfileSchema:
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(f"/users/{user_id}/")
            )
            .validate_status_code()
            .validate_json(user_profile_type_adapter)
        )
