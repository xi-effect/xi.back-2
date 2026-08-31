from typing import Any

import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag
from app.common.schemas.autocomplete_sch import TagKind
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio

tutor_id_filter_parametrization = pytest.mark.parametrize(
    "filter_by_tutor_id",
    [
        pytest.param(False, id="no_tutor_id_filter"),
        pytest.param(True, id="with_tutor_id_filter"),
    ],
)


@tutor_id_filter_parametrization
async def test_retrieving_multiple_tags(
    internal_client: TestClient,
    tutor_user_id: int,
    parametrized_tag_kind: TagKind,
    tutor_tag: AnyTag,
    tutor_tag_data: AnyJSON,
    other_tutor_tag: AnyTag,
    other_tutor_tag_data: AnyJSON,
    shared_tag: AnyTag,
    shared_tag_data: AnyJSON,
    outsider_tag: AnyTag,
    outsider_tag_data: AnyJSON,
    filter_by_tutor_id: bool,
) -> None:
    params: dict[str, Any] = {
        "tag_ids": [tutor_tag.id, other_tutor_tag.id, shared_tag.id, outsider_tag.id],
    }
    if filter_by_tutor_id:
        params["tutor_id"] = tutor_user_id

    assert_response(
        internal_client.get(
            f"/internal/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params=params,
        ),
        expected_json={
            str(tutor_tag.id): tutor_tag_data,
            str(other_tutor_tag.id): other_tutor_tag_data,
            str(shared_tag.id): shared_tag_data,
            str(outsider_tag.id): None if filter_by_tutor_id else outsider_tag_data,
        },
    )


@tutor_id_filter_parametrization
async def test_retrieving_multiple_tags_tag_not_found(
    internal_client: TestClient,
    tutor_user_id: int,
    parametrized_tag_kind: TagKind,
    deleted_tutor_tag_id: int,
    filter_by_tutor_id: bool,
) -> None:
    params: dict[str, Any] = {"tag_ids": [deleted_tutor_tag_id]}
    if filter_by_tutor_id:
        params["tutor_id"] = tutor_user_id

    assert_response(
        internal_client.get(
            f"/internal/autocomplete-service/tag-kinds/{parametrized_tag_kind}/tags/",
            params=params,
        ),
        expected_json={},
    )
