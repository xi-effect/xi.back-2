from typing import Annotated

from fastapi import Query

from app.autocomplete.dependencies.tags_dep import TagClassByKind
from app.autocomplete.models.tags_db import AnyTag
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.autocomplete_sch import TagSchema

router = APIRouterExt(tags=["tags internal"])


@router.get(
    "/tag-kinds/{tag_kind}/tags/",
    response_model=dict[str, TagSchema],
    summary="Retrieve multiple tags by ids",
)
async def retrieve_multiple_tags(
    tag_class: TagClassByKind,
    tag_ids: Annotated[list[int], Query(min_length=1, max_length=100)],
) -> dict[str, AnyTag]:
    return {
        str(tag.id): tag for tag in await tag_class.find_all_by_ids(tag_ids=tag_ids)
    }
