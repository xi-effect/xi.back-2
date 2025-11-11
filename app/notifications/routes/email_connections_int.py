from typing import Annotated

from fastapi import Path, Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.notifications.models.email_connections_db import EmailConnection

router = APIRouterExt(tags=["email connections internal"])


@router.put(
    path="/users/{user_id}/email-connection/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Create or update an email connection for any user by id",
)
async def create_or_update_email_connection(
    user_id: Annotated[int, Path()],
    data: EmailConnection.InputSchema,
    response: Response,
) -> None:
    email_connection = await EmailConnection.find_first_by_id(user_id)
    if email_connection is None:
        response.status_code = status.HTTP_201_CREATED
        await EmailConnection.create(
            user_id=user_id,
            **data.model_dump(),
        )
    else:
        email_connection.update(**data.model_dump())
