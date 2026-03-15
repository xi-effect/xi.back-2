from io import BytesIO

import aiofiles
from fastapi import UploadFile
from PIL import Image
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.filetype_ext import FILE_HEADER_SIZE, match_image_filetype
from app.users.dependencies.users_dep import AuthorizedUser
from app.users.models.users_db import User

router = APIRouterExt(tags=["current user avatar"])


class AvatarResponses(Responses):
    WRONG_FORMAT = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Invalid image format"


@router.put(
    "/users/current/avatar/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=AvatarResponses.responses(),
    summary="Upload a new user avatar",
)
async def update_or_create_avatar(
    user: AuthorizedUser,
    avatar: UploadFile,
) -> None:
    avatar_header_data = await avatar.read(FILE_HEADER_SIZE)

    if match_image_filetype(avatar_header_data) is None:
        raise AvatarResponses.WRONG_FORMAT

    await avatar.seek(0)
    avatar_image: Image.Image = Image.open(BytesIO(await avatar.read()))

    avatar_image = avatar_image.resize(User.avatar_shape)

    processed_avatar = BytesIO()
    avatar_image.save(processed_avatar, format="webp")
    processed_avatar.seek(0)

    async with aiofiles.open(user.avatar_path, "wb") as file:
        await file.write(processed_avatar.read())


@router.delete(
    "/users/current/avatar/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove current user avatar",
)
async def delete_avatar(user: AuthorizedUser) -> None:
    user.avatar_path.unlink(missing_ok=True)
