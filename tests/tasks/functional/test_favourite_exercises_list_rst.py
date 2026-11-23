from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.tasks.models.favourite_exercises_db import FavouriteExercise
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import remove_none_values

pytestmark = pytest.mark.anyio

FAVOURITE_EXERCISES_LIST_SIZE = 6


@pytest.fixture()
async def favourite_exercises(
    faker: Faker,
    active_session: ActiveSession,
    authorized_user_id: int,
) -> AsyncIterator[Sequence[FavouriteExercise]]:
    created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    favourite_exercises: list[FavouriteExercise] = []

    async with active_session():
        for i in range(FAVOURITE_EXERCISES_LIST_SIZE):
            if i != FAVOURITE_EXERCISES_LIST_SIZE - 1:
                created_at -= timedelta(minutes=faker.random_int(min=1))
            favourite_exercises.append(
                await FavouriteExercise.create(
                    user_id=authorized_user_id,
                    exercise_id=uuid4(),
                    created_at=created_at,
                )
            )

    favourite_exercises.sort(
        key=lambda favourite_exercise: (
            favourite_exercise.created_at,
            favourite_exercise.exercise_id,
        ),
        reverse=True,
    )

    yield favourite_exercises

    async with active_session():
        await FavouriteExercise.delete_by_kwargs(user_id=authorized_user_id)


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, FAVOURITE_EXERCISES_LIST_SIZE, id="start_to_end"),
        pytest.param(0, FAVOURITE_EXERCISES_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            FAVOURITE_EXERCISES_LIST_SIZE // 2,
            FAVOURITE_EXERCISES_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_favourite_exercises_listing(
    authorized_client: TestClient,
    favourite_exercises: Sequence[FavouriteExercise],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/task-service/users/current/favourite-exercises/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else favourite_exercises[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            FavouriteExercise.ResponseSchema.model_validate(
                favourite_exercise, from_attributes=True
            )
            for favourite_exercise in favourite_exercises[offset:limit]
        ],
    )


async def test_favourite_exercises_listing_empty_list(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/task-service/users/current/favourite-exercises/",
            params={"limit": 1},
        ),
        expected_json=[],
    )
