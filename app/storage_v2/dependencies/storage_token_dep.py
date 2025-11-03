from typing import Annotated

from fastapi import Depends, Header
from starlette import status

from app.common.config import storage_token_provider
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.schemas.storage_sch import StorageTokenPayloadSchema


class StorageTokenResponses(Responses):
    INVALID_STORAGE_TOKEN = status.HTTP_403_FORBIDDEN, "Invalid storage token"


@with_responses(StorageTokenResponses)
def validate_and_deserialize_storage_token(
    x_storage_token: Annotated[str, Header()],
    auth_data: AuthorizationData,
) -> StorageTokenPayloadSchema:
    storage_token_payload = storage_token_provider.validate_and_deserialize(
        token=x_storage_token
    )
    if storage_token_payload is None:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

    if (
        storage_token_payload.user_id is not None
        and auth_data.user_id != storage_token_payload.user_id
    ):
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

    return storage_token_payload


StorageTokenPayload = Annotated[
    StorageTokenPayloadSchema, Depends(validate_and_deserialize_storage_token)
]
