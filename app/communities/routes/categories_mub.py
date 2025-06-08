from collections.abc import Sequence
from typing import Annotated

from fastapi import Body, HTTPException
from starlette import status

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.categories_dep import CategoryById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.categories_db import Category
from app.communities.responses import LimitedListResponses, MoveResponses

router = APIRouterExt(tags=["categories mub"])


@router.get(
    "/communities/{community_id}/categories/",
    response_model=list[Category.ResponseSchema],
    summary="List categories in the community (in user-defined order)",
)
async def list_categories(community: CommunityById) -> Sequence[Category]:
    return await Category.find_all_by_community_id(community_id=community.id)


@router.put(
    "/communities/{community_id}/categories/positions/",
    status_code=204,
    summary="Reindex categories in a community",
)
async def reindex_categories(community: CommunityById) -> None:
    await Category.reindex_by_list_id(list_id=community.id)


@router.post(
    "/communities/{community_id}/categories/",
    status_code=201,
    response_model=Category.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new category in the community (append to the end of the list)",
)
async def create_category(
    community: CommunityById, data: Category.InputSchema
) -> Category:
    if await Category.is_limit_per_community_reached(community_id=community.id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await Category.create(community_id=community.id, **data.model_dump())


@router.get(
    "/categories/{category_id}/",
    response_model=Category.ResponseSchema,
    summary="Retrieve any category by id",
)
async def retrieve_category(category: CategoryById) -> Category:
    return category


@router.patch(
    "/categories/{category_id}/",
    response_model=Category.ResponseSchema,
    summary="Update any category by id",
)
async def patch_category(
    category: CategoryById, data: Category.PatchSchema
) -> Category:
    category.update(**data.model_dump(exclude_defaults=True))
    return category


@router.put(
    "/categories/{category_id}/position/",
    status_code=204,
    responses=MoveResponses.responses(),
    summary="Move category to a new position",
)
async def move_category(
    category: CategoryById,
    after_id: Annotated[int | None, Body()] = None,
    before_id: Annotated[int | None, Body()] = None,
) -> None:
    try:
        await category.validate_and_move(
            list_id=category.list_id,
            after_id=after_id,
            before_id=before_id,
        )
    except InvalidMoveException as e:  # TODO (33602197) pragma: no cover
        raise HTTPException(status.HTTP_409_CONFLICT, e.message)


@router.delete(
    "/categories/{category_id}/",
    status_code=204,
    summary="Delete any category by id",
)
async def delete_category(category: CategoryById) -> None:
    await category.delete()
