from typing import Any

import pytest
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag, Tag
from app.common.schemas.autocomplete_sch import TagKind
from tests.autocomplete import factories
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_tag_creation(
    active_session: ActiveSession,
    tutor_user_id: int,
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    tag_class: type[AnyTag],
) -> None:
    tag_input_data = factories.TagInputFactory.build_json()

    tag_id: int = assert_response(
        tutor_client.post(
            "/api/protected/autocomplete-service/roles/tutor"
            f"/tag-kinds/{parametrized_tag_kind}/tags/",
            json=tag_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **tag_input_data,
            "id": int,
            "tutor_id": tutor_user_id,
        },
    ).json()["id"]

    async with active_session():
        tag = await tag_class.find_first_by_id(tag_id)
        assert tag is not None
        await tag.delete()


async def test_tag_creation_quantity_exceeded(
    mock_stack: MockStack,
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    tutor_tag: AnyTag,
) -> None:
    mock_stack.enter_mock(Tag, "max_count_per_tutor_per_kind", property_value=1)

    assert_response(
        tutor_client.post(
            "/api/protected/autocomplete-service/roles/tutor"
            f"/tag-kinds/{parametrized_tag_kind}/tags/",
            json=factories.TagInputFactory.build_json(),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


async def test_tag_updating(
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    tutor_tag_data: AnyJSON,
) -> None:
    patch_tag_data = factories.TagPatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            "/api/protected/autocomplete-service/roles/tutor"
            f"/tag-kinds/{parametrized_tag_kind}/tags/{tutor_tag_data["id"]}/",
            json=patch_tag_data,
        ),
        expected_json={
            **tutor_tag_data,
            **patch_tag_data,
        },
    )


async def test_tag_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    tag_class: type[AnyTag],
    tutor_tag: AnyTag,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/autocomplete-service/roles/tutor"
            f"/tag-kinds/{parametrized_tag_kind}/tags/{tutor_tag.id}/"
        )
    )

    async with active_session():
        assert await tag_class.find_first_by_id(tutor_tag.id) is None


@pytest.mark.parametrize(
    ("method", "to_tag_id", "body_factory"),
    [
        pytest.param("POST", False, factories.TagInputFactory, id="create"),
        pytest.param("PATCH", True, factories.TagPatchFactory, id="update"),
    ],
)
@pytest.mark.parametrize(
    "existing_tag",
    [
        pytest.param(lf("other_tutor_tag"), id="other_tutor_tag"),
        pytest.param(lf("shared_tag"), id="shared_tag"),
    ],
)
async def test_tag_already_existing(
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    tutor_tag: AnyTag,
    method: str,
    to_tag_id: bool,
    body_factory: type[BaseModelFactory[Any]],
    existing_tag: AnyTag,
) -> None:
    postfix = f"{tutor_tag.id}/" if to_tag_id else ""

    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/autocomplete-service/roles/tutor"
                f"/tag-kinds/{parametrized_tag_kind}/tags/{postfix}"
            ),
            json=body_factory.build_json(name=existing_tag.name),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Tag already exists"},
    )


tag_request_parametrization = pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PATCH", factories.TagPatchFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)


@tag_request_parametrization
async def test_tag_not_finding(
    tutor_client: TestClient,
    parametrized_tag_kind: TagKind,
    deleted_tutor_tag_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/autocomplete-service/roles/tutor"
                f"/tag-kinds/{parametrized_tag_kind}/tags/{deleted_tutor_tag_id}/"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tag not found"},
    )


@tag_request_parametrization
@pytest.mark.parametrize(
    "foreign_tag",
    [
        pytest.param(lf("tutor_tag"), id="tutor_tag"),
        pytest.param(lf("shared_tag"), id="shared_tag"),
    ],
)
async def test_tag_access_denied(
    outsider_client: TestClient,
    parametrized_tag_kind: TagKind,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    foreign_tag: AnyTag,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=(
                "/api/protected/autocomplete-service/roles/tutor"
                f"/tag-kinds/{parametrized_tag_kind}/tags/{foreign_tag.id}/"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Tag access denied"},
    )
