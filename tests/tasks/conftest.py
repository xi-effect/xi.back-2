from collections.abc import AsyncIterator
from datetime import timezone
from uuid import UUID, uuid4

import pytest
from faker import Faker

from app.tasks.models.favourite_exercises_db import FavouriteExercise
from tests.common.active_session import ActiveSession


@pytest.fixture()
def exercise_id() -> UUID:
    return uuid4()


@pytest.fixture()
async def favourite_exercise(
    faker: Faker,
    active_session: ActiveSession,
    authorized_user_id: int,
    exercise_id: UUID,
) -> AsyncIterator[FavouriteExercise]:
    async with active_session():
        favourite_exercise = await FavouriteExercise.create(
            user_id=authorized_user_id,
            exercise_id=exercise_id,
            created_at=faker.date_time_between(tzinfo=timezone.utc),
        )

    yield favourite_exercise

    async with active_session():
        await FavouriteExercise.delete_by_kwargs(
            user_id=authorized_user_id,
            exercise_id=exercise_id,
        )
