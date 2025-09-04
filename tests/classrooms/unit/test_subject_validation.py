import pytest
from faker import Faker
from fastapi import HTTPException
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status

from app.classrooms.routes.classrooms_tutor_rst import (
    SubjectResponses,
    validate_subject,
)
from app.common.config import settings
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import PytestRequest
from tests.factories import SubjectFactory

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def new_subject_id(faker: Faker) -> int:
    return faker.random_int()


@pytest.fixture(
    params=[
        pytest.param(True, id="with_old_subject"),
        pytest.param(False, id="no_old_subject"),
    ]
)
async def old_subject_id(
    faker: Faker, new_subject_id: int, request: PytestRequest[bool]
) -> int | None:
    return new_subject_id + faker.random_int(min=1) if request.param else None


async def test_subject_validation(
    faker: Faker,
    autocomplete_respx_mock: MockRouter,
    new_subject_id: int,
    old_subject_id: int | None,
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        f"/subjects/{new_subject_id}/"
    ).respond(json=SubjectFactory.build_json())

    await validate_subject(
        new_subject_id=new_subject_id,
        old_subject_id=old_subject_id,
    )

    assert_last_httpx_request(
        autocomplete_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_subject_validation_subject_not_found(
    autocomplete_respx_mock: MockRouter,
    new_subject_id: int,
    old_subject_id: int | None,
) -> None:
    autocomplete_bridge_mock = autocomplete_respx_mock.get(
        f"/subjects/{new_subject_id}/"
    ).respond(
        status_code=status.HTTP_404_NOT_FOUND,
        json={"detail": "Subject not found"},
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_subject(
            new_subject_id=new_subject_id,
            old_subject_id=old_subject_id,
        )

    assert_contains(exc_info, {"value": SubjectResponses.SUBJECT_NOT_FOUND})

    assert_last_httpx_request(
        autocomplete_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_subject_validation_subject_has_not_changed(
    autocomplete_respx_mock: MockRouter,
    new_subject_id: int,
) -> None:
    await validate_subject(
        new_subject_id=new_subject_id,
        old_subject_id=new_subject_id,
    )

    autocomplete_respx_mock.calls.assert_not_called()


async def test_subject_validation_subject_is_none(
    autocomplete_respx_mock: MockRouter,
    old_subject_id: int | None,
) -> None:
    await validate_subject(
        new_subject_id=None,
        old_subject_id=old_subject_id,
    )

    autocomplete_respx_mock.calls.assert_not_called()
