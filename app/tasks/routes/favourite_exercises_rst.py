from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Path
from pydantic import AwareDatetime, Field
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.tasks.models.favourite_exercises_db import FavouriteExercise

router = APIRouterExt(tags=["favourite exercises"])


@router.get(
    path="/users/current/favourite-exercises/",
    response_model=list[FavouriteExercise.ResponseSchema],
    summary="List paginated favourite exercises for the current user",
)
async def list_favourite_exercises(
    auth_data: AuthorizationData,
    created_before: AwareDatetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Sequence[FavouriteExercise]:
    return await FavouriteExercise.find_paginated_by_user_id(
        user_id=auth_data.user_id,
        created_before=created_before,
        limit=limit,
    )


@router.put(
    path="/users/current/favourite-exercises/{exercise_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add an exercise to current user's favourites by id",
)
async def add_favourite_exercise(
    auth_data: AuthorizationData,
    exercise_id: Annotated[UUID, Path()],
) -> None:
    await FavouriteExercise.upsert_by_ids(
        user_id=auth_data.user_id,
        exercise_id=exercise_id,
    )


@router.delete(
    path="/users/current/favourite-exercises/{exercise_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an exercise from current user's favourites by id",
)
async def remove_favourite_exercise(
    auth_data: AuthorizationData,
    exercise_id: Annotated[UUID, Path()],
) -> None:
    await FavouriteExercise.delete_by_kwargs(
        user_id=auth_data.user_id,
        exercise_id=exercise_id,
    )
