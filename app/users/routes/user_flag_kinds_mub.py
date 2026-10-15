from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from pydantic_marshals.base import PatchDefault
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.users.dependencies.user_flag_kinds_dep import UserFlagKindByID
from app.users.models.user_flag_kinds_db import UserFlagKind

router = APIRouterExt(tags=["user flag kinds mub"])


@router.get(
    "/user-flag-kinds/",
    response_model=list[UserFlagKind.ResponseSchema],
    summary="List paginated user flag kinds",
)
async def list_user_flag_kinds(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Sequence[UserFlagKind]:
    return await UserFlagKind.find_paginated_by_kwargs(
        offset,
        limit,
        UserFlagKind.id.asc(),
    )


class UserFlagKindConflictResponses(Responses):
    USER_FLAG_KIND_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "User flag kind already exists",
    )


@router.post(
    "/user-flag-kinds/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserFlagKind.ResponseSchema,
    responses=UserFlagKindConflictResponses.responses(),
    summary="Create a new user flag kind",
)
async def create_user_flag_kind(data: UserFlagKind.InputSchema) -> UserFlagKind:
    if await UserFlagKind.is_present_by_key(key=data.key):
        raise UserFlagKindConflictResponses.USER_FLAG_KIND_ALREADY_EXISTS
    return await UserFlagKind.create(**data.model_dump())


@router.get(
    "/user-flag-kinds/{user_flag_kind_id}/",
    response_model=UserFlagKind.ResponseSchema,
    summary="Retrieve any user flag kind by id",
)
async def retrieve_user_flag_kind(user_flag_kind: UserFlagKindByID) -> UserFlagKind:
    return user_flag_kind


@router.patch(
    "/user-flag-kinds/{user_flag_kind_id}/",
    response_model=UserFlagKind.ResponseSchema,
    responses=UserFlagKindConflictResponses.responses(),
    summary="Update any user flag kind by id",
)
async def update_user_flag_kind(
    user_flag_kind: UserFlagKindByID,
    data: UserFlagKind.PatchSchema,
) -> UserFlagKind:
    if (
        data.key is not PatchDefault
        and data.key != user_flag_kind.key
        and await UserFlagKind.is_present_by_key(key=data.key)
    ):
        raise UserFlagKindConflictResponses.USER_FLAG_KIND_ALREADY_EXISTS
    user_flag_kind.update(**data.model_dump(exclude_defaults=True))
    return user_flag_kind


@router.delete(
    "/user-flag-kinds/{user_flag_kind_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any user flag kind by id",
)
async def delete_user_flag_kind(user_flag_kind: UserFlagKindByID) -> None:
    await user_flag_kind.delete()
