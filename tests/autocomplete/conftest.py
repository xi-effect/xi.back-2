import string
from collections.abc import AsyncIterator
from typing import Final

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.autocomplete.models.subjects_db import Subject
from app.common.dependencies.authorization_dep import ProxyAuthData
from tests.autocomplete import factories
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory


@pytest.fixture()
def tutor_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def tutor_user_id(tutor_auth_data: ProxyAuthData) -> int:
    return tutor_auth_data.user_id


@pytest.fixture()
def tutor_client(client: TestClient, tutor_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=tutor_auth_data.as_headers)


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
async def subject(active_session: ActiveSession, tutor_user_id: int) -> Subject:
    async with active_session():
        return await Subject.create(
            **factories.SubjectInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )


@pytest.fixture()
async def subject_mub_data(subject: Subject) -> AnyJSON:
    return Subject.ResponseMUBSchema.model_validate(subject).model_dump(mode="json")


@pytest.fixture()
async def subject_data(subject: Subject) -> AnyJSON:
    return Subject.ResponseSchema.model_validate(subject).model_dump(mode="json")


@pytest.fixture()
async def deleted_subject_id(active_session: ActiveSession, subject: Subject) -> int:
    async with active_session():
        await subject.delete()
    return subject.id


SUBJECT_LIST_SIZE: Final[int] = 8


def quarter_of_ascii_letters_any_case(quarter_index: int) -> str:
    letters = string.ascii_lowercase[quarter_index::4]
    return letters + letters.upper()


@pytest.fixture()
async def common_subject_name_prefix(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(0))


@pytest.fixture()
async def even_subject_name_suffix(faker: Faker) -> str:
    return faker.bothify("###")


@pytest.fixture()
async def odd_subject_name_suffix(faker: Faker) -> str:
    return faker.bothify("??%", letters=quarter_of_ascii_letters_any_case(1))


@pytest.fixture()
async def excluded_from_subject_names(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(2))


def generate_subject_name(
    faker: Faker,
    prefix: str,
    suffix: str,
) -> str:
    random_part: str = faker.bothify(
        "?" * faker.random_int(min=0, max=90),
        letters=quarter_of_ascii_letters_any_case(3),
    )
    return prefix + random_part + suffix


@pytest.fixture()
async def subjects(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    common_subject_name_prefix: str,
    even_subject_name_suffix: str,
    odd_subject_name_suffix: str,
) -> AsyncIterator[list[Subject]]:
    subjects: list[Subject] = []
    async with active_session():
        for i in range(SUBJECT_LIST_SIZE):
            subjects.append(
                await Subject.create(
                    name=generate_subject_name(
                        faker=faker,
                        prefix=common_subject_name_prefix,
                        suffix=(
                            even_subject_name_suffix
                            if i % 2 == 0
                            else odd_subject_name_suffix
                        ),
                    ),
                    tutor_id=None if i % 2 == 0 else tutor_user_id,
                )
            )

    subjects.sort(key=lambda subject: subject.name)
    yield subjects

    async with active_session():
        for subject in subjects:
            await subject.delete()
