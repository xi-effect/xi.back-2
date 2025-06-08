from typing import Annotated

import filetype  # type: ignore[import-untyped]
from fastapi import File, UploadFile
from filetype.types.image import Webp  # type: ignore[import-untyped]
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.communities_dep import CommunityById

router = APIRouterExt(tags=["community avatars"])


class AvatarResponses(Responses):
    WRONG_FORMAT = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Invalid image format"


# TODO authorize a user in the community
@router.put(
    "/communities/{community_id}/avatar/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=AvatarResponses.responses(),
    summary="Update or create a community avatar by id",
)
async def update_or_create_avatar(
    community: CommunityById,
    avatar: Annotated[UploadFile, File(description="image/webp")],
) -> None:
    if not filetype.match(avatar.file, [Webp()]):
        raise AvatarResponses.WRONG_FORMAT

    with community.avatar_path.open("wb") as file:
        file.write(await avatar.read())


@router.delete(
    "/communities/{community_id}/avatar/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a community avatar by id",
)
async def delete_avatar(community: CommunityById) -> None:
    community.avatar_path.unlink(missing_ok=True)
