from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag
from app.common.schemas.autocomplete_sch import TagKind
from tests.autocomplete import factories
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_tag_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    tag_class: type[AnyTag],
) -> None:
    tag_input_data = factories.TagInputMUBFactory.build_json()

    tag_id: int = assert_response(
        mub_client.post(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            json=tag_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **tag_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        tag = await tag_class.find_first_by_id(tag_id)
        assert tag is not None
        await tag.delete()


async def test_tag_creation_tag_already_exists(
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    tutor_tag_mub_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            json=tutor_tag_mub_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Tag already exists"},
    )


async def test_tag_updating(
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    tutor_tag_mub_data: AnyJSON,
) -> None:
    patch_tag_data = factories.TagPatchMUBFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/{tutor_tag_mub_data["id"]}/",
            json=patch_tag_data,
        ),
        expected_json={
            **tutor_tag_mub_data,
            **patch_tag_data,
        },
    )


async def test_tag_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    tag_class: type[AnyTag],
    tutor_tag: AnyTag,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/{tutor_tag.id}/"
        )
    )

    async with active_session():
        assert await tag_class.find_first_by_id(tutor_tag.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PATCH", factories.TagPatchMUBFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_tag_not_finding(
    mub_client: TestClient,
    parametrized_tag_kind: TagKind,
    deleted_tutor_tag_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/{deleted_tutor_tag_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tag not found"},
    )
