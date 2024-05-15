from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.categories_dep import CategoryById
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.categories_db import Category

router = APIRouterExt(tags=["categories mub"])


@router.get(
    "/communities/{community_id}/categories/",
    response_model=list[Category.ResponseSchema],
    summary="List categories in the community (in user-defined order)",
)
async def list_categories(community: CommunityById) -> Sequence[Category]:
    return await Category.find_all_by_community_id(community_id=community.id)


@router.post(
    "/communities/{community_id}/categories/",
    status_code=201,
    response_model=Category.ResponseSchema,
    summary="Create a new category in the community (append to the end of the list)",
)
async def create_category(
    community: CommunityById, data: Category.InputSchema
) -> Category:
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


@router.delete(
    "/categories/{category_id}/",
    status_code=204,
    summary="Delete any category by id",
)
async def delete_category(category: CategoryById) -> None:
    await category.delete()
