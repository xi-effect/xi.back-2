import string
from collections.abc import AsyncIterator
from typing import Final

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import SubjectTag, Tag
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
async def subject_tag(
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[SubjectTag]:
    async with active_session():
        subject_tag: SubjectTag = await SubjectTag.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )

    yield subject_tag

    async with active_session():
        await SubjectTag.delete_by_kwargs(id=subject_tag.id)


@pytest.fixture()
async def subject_tag_mub_data(subject_tag: SubjectTag) -> AnyJSON:
    return Tag.ResponseMUBSchema.model_validate(subject_tag).model_dump(mode="json")


@pytest.fixture()
async def subject_tag_data(subject_tag: SubjectTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(subject_tag).model_dump(mode="json")


@pytest.fixture()
async def other_subject_tag(
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[SubjectTag]:
    async with active_session():
        other_subject_tag: SubjectTag = await SubjectTag.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )

    yield other_subject_tag

    async with active_session():
        await SubjectTag.delete_by_kwargs(id=other_subject_tag.id)


@pytest.fixture()
async def other_subject_tag_data(other_subject_tag: SubjectTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(other_subject_tag).model_dump(mode="json")


@pytest.fixture()
async def deleted_subject_tag_id(
    active_session: ActiveSession, subject_tag: SubjectTag
) -> int:
    async with active_session():
        await subject_tag.delete()
    return subject_tag.id


SUBJECT_TAG_LIST_SIZE: Final[int] = 8


def quarter_of_ascii_letters_any_case(quarter_index: int) -> str:
    letters = string.ascii_lowercase[quarter_index::4]
    return letters + letters.upper()


@pytest.fixture()
async def common_subject_tag_name_prefix(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(0))


@pytest.fixture()
async def even_subject_tag_name_suffix(faker: Faker) -> str:
    return faker.bothify("###")


@pytest.fixture()
async def odd_subject_tag_name_suffix(faker: Faker) -> str:
    return faker.bothify("??%", letters=quarter_of_ascii_letters_any_case(1))


@pytest.fixture()
async def excluded_from_subject_tag_names(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(2))


def generate_subject_tag_name(
    faker: Faker,
    prefix: str,
    suffix: str,
    unique_letter: str,
) -> str:
    random_part: str = faker.bothify(
        "?" * faker.random_int(min=0, max=90),
        letters=quarter_of_ascii_letters_any_case(3),
    )
    return prefix + random_part + unique_letter + suffix


@pytest.fixture()
async def subject_tags(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    common_subject_tag_name_prefix: str,
    even_subject_tag_name_suffix: str,
    odd_subject_tag_name_suffix: str,
) -> AsyncIterator[list[SubjectTag]]:
    subject_tags: list[SubjectTag] = []
    unique_letters = quarter_of_ascii_letters_any_case(3)
    async with active_session():
        for i in range(SUBJECT_TAG_LIST_SIZE):
            subject_tags.append(
                await SubjectTag.create(
                    name=generate_subject_tag_name(
                        faker=faker,
                        prefix=common_subject_tag_name_prefix,
                        suffix=(
                            even_subject_tag_name_suffix
                            if i % 2 == 0
                            else odd_subject_tag_name_suffix
                        ),
                        unique_letter=unique_letters[i],
                    ),
                    tutor_id=None if i % 2 == 0 else tutor_user_id,
                )
            )

    subject_tags.sort(key=lambda subject_tag: subject_tag.name)
    yield subject_tags

    async with active_session():
        for subject_tag in subject_tags:
            await subject_tag.delete()
