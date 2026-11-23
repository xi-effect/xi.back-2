from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.tasks.models.favourite_exercises_db import FavouriteExercise
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response

pytestmark = pytest.mark.anyio

existing_favourite_exercise_parametrization = pytest.mark.parametrize(
    "existing_favourite_exercise",
    [
        pytest.param(None, id="no_existing_favourite_exercise"),
        pytest.param(lf("favourite_exercise"), id="existing_favourite_exercise"),
    ],
)


@existing_favourite_exercise_parametrization
@freeze_time()
async def test_favourite_exercise_adding(
    active_session: ActiveSession,
    authorized_client: TestClient,
    authorized_user_id: int,
    exercise_id: UUID,
    existing_favourite_exercise: FavouriteExercise | None,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/protected/task-service/users/current/favourite-exercises"
            f"/{exercise_id}/",
        ),
    )

    async with active_session():
        favourite_exercise = await FavouriteExercise.find_first_by_kwargs(
            user_id=authorized_user_id,
            exercise_id=exercise_id,
        )
        assert favourite_exercise is not None
        assert_contains(
            favourite_exercise,
            {
                "created_at": (
                    datetime_utc_now()
                    if existing_favourite_exercise is None
                    else existing_favourite_exercise.created_at
                )
            },
        )

        await FavouriteExercise.delete_by_kwargs(
            user_id=authorized_user_id,
            exercise_id=exercise_id,
        )


@existing_favourite_exercise_parametrization
async def test_favourite_exercise_removing(
    active_session: ActiveSession,
    authorized_client: TestClient,
    authorized_user_id: int,
    exercise_id: UUID,
    existing_favourite_exercise: FavouriteExercise | None,
) -> None:
    assert_nodata_response(
        authorized_client.delete(
            "/api/protected/task-service/users/current/favourite-exercises"
            f"/{exercise_id}/",
        ),
    )

    async with active_session():
        assert (
            await FavouriteExercise.find_first_by_kwargs(
                user_id=authorized_user_id,
                exercise_id=exercise_id,
            )
            is None
        )
