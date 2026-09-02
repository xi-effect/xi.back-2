import string
from collections.abc import AsyncIterator
from typing import Final, assert_never

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag, GenericTag, SubjectTag, Tag
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.autocomplete_sch import TagKind
from tests.autocomplete import factories
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
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
def outsider_user_id(outsider_auth_data: ProxyAuthData) -> int:
    return outsider_auth_data.user_id


@pytest.fixture()
def outsider_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture(params=[TagKind.SUBJECT, TagKind.GENERIC])
def parametrized_tag_kind(request: PytestRequest[TagKind]) -> TagKind:
    return request.param


@pytest.fixture()
def tag_class(parametrized_tag_kind: TagKind) -> type[AnyTag]:
    match parametrized_tag_kind:
        case TagKind.SUBJECT:
            return SubjectTag
        case TagKind.GENERIC:
            return GenericTag
        case _:
            assert_never(parametrized_tag_kind)


@pytest.fixture()
async def tutor_tag(
    active_session: ActiveSession,
    tutor_user_id: int,
    tag_class: type[AnyTag],
) -> AsyncIterator[AnyTag]:
    async with active_session():
        tutor_tag: AnyTag = await tag_class.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )

    yield tutor_tag

    async with active_session():
        await tag_class.delete_by_kwargs(id=tutor_tag.id)


@pytest.fixture()
async def tutor_tag_mub_data(tutor_tag: AnyTag) -> AnyJSON:
    return Tag.ResponseMUBSchema.model_validate(tutor_tag).model_dump(mode="json")


@pytest.fixture()
async def tutor_tag_data(tutor_tag: AnyTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(tutor_tag).model_dump(mode="json")


@pytest.fixture()
async def other_tutor_tag(
    active_session: ActiveSession,
    tutor_user_id: int,
    tag_class: type[AnyTag],
) -> AsyncIterator[AnyTag]:
    async with active_session():
        other_tutor_tag: AnyTag = await tag_class.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )

    yield other_tutor_tag

    async with active_session():
        await tag_class.delete_by_kwargs(id=other_tutor_tag.id)


@pytest.fixture()
async def other_tutor_tag_data(other_tutor_tag: AnyTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(other_tutor_tag).model_dump(mode="json")


@pytest.fixture()
async def shared_tag(
    active_session: ActiveSession,
    tag_class: type[AnyTag],
) -> AsyncIterator[AnyTag]:
    async with active_session():
        shared_tag: AnyTag = await tag_class.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=None,
        )

    yield shared_tag

    async with active_session():
        await tag_class.delete_by_kwargs(id=shared_tag.id)


@pytest.fixture()
async def shared_tag_data(shared_tag: AnyTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(shared_tag).model_dump(mode="json")


@pytest.fixture()
async def outsider_tag(
    active_session: ActiveSession,
    outsider_user_id: int,
    tag_class: type[AnyTag],
) -> AsyncIterator[AnyTag]:
    async with active_session():
        outsider_tag: AnyTag = await tag_class.create(
            **factories.TagInputFactory.build_python(),
            tutor_id=outsider_user_id,
        )

    yield outsider_tag

    async with active_session():
        await tag_class.delete_by_kwargs(id=outsider_tag.id)


@pytest.fixture()
async def outsider_tag_data(outsider_tag: AnyTag) -> AnyJSON:
    return Tag.ResponseSchema.model_validate(outsider_tag).model_dump(mode="json")


@pytest.fixture()
async def deleted_tutor_tag_id(active_session: ActiveSession, tutor_tag: AnyTag) -> int:
    async with active_session():
        await tutor_tag.delete()
    return tutor_tag.id


TAG_LIST_SIZE: Final[int] = 8


def quarter_of_ascii_letters_any_case(quarter_index: int) -> str:
    letters = string.ascii_lowercase[quarter_index::4]
    return letters + letters.upper()


@pytest.fixture()
async def common_tag_name_prefix(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(0))


@pytest.fixture()
async def even_tag_name_suffix(faker: Faker) -> str:
    return faker.bothify("###")


@pytest.fixture()
async def odd_tag_name_suffix(faker: Faker) -> str:
    return faker.bothify("??%", letters=quarter_of_ascii_letters_any_case(1))


@pytest.fixture()
async def excluded_from_tag_names(faker: Faker) -> str:
    return faker.bothify("???", letters=quarter_of_ascii_letters_any_case(2))


def generate_tag_name(
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
async def tags(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    tag_class: type[AnyTag],
    common_tag_name_prefix: str,
    even_tag_name_suffix: str,
    odd_tag_name_suffix: str,
) -> AsyncIterator[list[AnyTag]]:
    tags: list[AnyTag] = []
    unique_letters = quarter_of_ascii_letters_any_case(3)
    async with active_session():
        for i in range(TAG_LIST_SIZE):
            tags.append(
                await tag_class.create(
                    **factories.TagInputFactory.build_python(
                        name=generate_tag_name(
                            faker=faker,
                            prefix=common_tag_name_prefix,
                            suffix=(
                                even_tag_name_suffix
                                if i % 2 == 0
                                else odd_tag_name_suffix
                            ),
                            unique_letter=unique_letters[i],
                        ),
                    ),
                    tutor_id=None if i % 2 == 0 else tutor_user_id,
                )
            )

    tags.sort(key=lambda tag: tag.name)
    yield tags

    async with active_session():
        for tag in tags:
            await tag.delete()
