from typing import Annotated

import filetype  # type: ignore[import-untyped]
from fastapi import File, UploadFile
from filetype.types.image import Webp  # type: ignore[import-untyped]
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.users_dep import AuthorizedUser

router = APIRouterExt(tags=["current user avatar"])


class AvatarResponses(Responses):
    WRONG_FORMAT = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Invalid image format"


@router.put(
    "/users/current/avatar/",
    status_code=204,
    responses=AvatarResponses.responses(),
    summary="Upload a new user avatar",
)
async def update_or_create_avatar(
    user: AuthorizedUser,
    avatar: Annotated[UploadFile, File(description="image/webp")],
) -> None:
    if not filetype.match(avatar.file, [Webp()]):
        raise AvatarResponses.WRONG_FORMAT

    with user.avatar_path.open("wb") as file:
        file.write(await avatar.read())


@router.delete(
    "/users/current/avatar/",
    status_code=204,
    summary="Remove current user avatar",
)
async def delete_avatar(user: AuthorizedUser) -> None:
    user.avatar_path.unlink(missing_ok=True)
