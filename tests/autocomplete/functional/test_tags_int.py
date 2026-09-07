from typing import Any

import pytest
from starlette.testclient import TestClient

from app.autocomplete.models.tags_db import AnyTag
from app.common.schemas.autocomplete_sch import TagKind, TagSchema
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import repackage_json

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
    other_tutor_tag: AnyTag,
    shared_tag: AnyTag,
    outsider_tag: AnyTag,
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
            str(tutor_tag.id): repackage_json(TagSchema, tutor_tag),
            str(other_tutor_tag.id): repackage_json(TagSchema, other_tutor_tag),
            str(shared_tag.id): repackage_json(TagSchema, shared_tag),
            str(outsider_tag.id): (
                None if filter_by_tutor_id else repackage_json(TagSchema, outsider_tag)
            ),
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
