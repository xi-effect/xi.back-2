from typing import Annotated

from fastapi import Depends, Header
from starlette import status

from app.common.config import content_token_provider
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.common.schemas.content_sch import ContentTokenPayloadSchema


class ContentTokenResponses(Responses):
    INVALID_CONTENT_TOKEN = status.HTTP_403_FORBIDDEN, "Invalid content token"


@with_responses(ContentTokenResponses)
def validate_and_deserialize_content_token(
    x_content_token: Annotated[str, Header()],
    auth_data: AuthorizationData,
) -> ContentTokenPayloadSchema:
    content_token_payload = content_token_provider.validate_and_deserialize(
        token=x_content_token
    )
    if content_token_payload is None:
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN

    if (
        content_token_payload.user_id is not None
        and auth_data.user_id != content_token_payload.user_id
    ):
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN

    return content_token_payload


ContentTokenPayload = Annotated[
    ContentTokenPayloadSchema, Depends(validate_and_deserialize_content_token)
]


class InsufficientPermissionsResponses(Responses):
    INSUFFICIENT_PERMISSIONS = (
        status.HTTP_403_FORBIDDEN,
        "Insufficient content token permissions",
    )


@with_responses(InsufficientPermissionsResponses)
async def ensure_content_token_allows_uploading_files(
    content_token_payload: ContentTokenPayload,
) -> ContentTokenPayloadSchema:
    if not content_token_payload.can_upload_files:
        raise InsufficientPermissionsResponses.INSUFFICIENT_PERMISSIONS
    return content_token_payload


@with_responses(InsufficientPermissionsResponses)
async def ensure_content_token_allows_reading_files(
    content_token_payload: ContentTokenPayload,
) -> ContentTokenPayloadSchema:
    if not content_token_payload.can_read_files:
        raise InsufficientPermissionsResponses.INSUFFICIENT_PERMISSIONS
    return content_token_payload
