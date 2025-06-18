from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.categories_db import Category


class CategoriesResponses(Responses):
    CATEGORY_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Category not found"


@with_responses(CategoriesResponses)
async def get_category_by_id(category_id: Annotated[int, Path()]) -> Category:
    category = await Category.find_first_by_id(category_id)
    if category is None:
        raise CategoriesResponses.CATEGORY_NOT_FOUND
    return category


CategoryById = Annotated[Category, Depends(get_category_by_id)]


@with_responses(CategoriesResponses)
async def validate_optional_category_id(
    community: CommunityById, category_id: int | None = None
) -> int | None:
    if category_id is None:
        return None

    category = await Category.find_first_by_kwargs(
        id=category_id, community_id=community.id
    )
    if category is None:  # TODO (33602197) pragma: no cover
        raise CategoriesResponses.CATEGORY_NOT_FOUND
    return category.id


ValidatedOptionalCategoryId = Annotated[
    int | None, Depends(validate_optional_category_id)
]
