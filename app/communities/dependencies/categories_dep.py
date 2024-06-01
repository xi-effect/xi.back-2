from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.categories_db import Category


class CategoriesResponses(Responses):
    CATEGORY_NOT_FOUND = 404, "Category not found"


@with_responses(CategoriesResponses)
async def get_category_by_id(category_id: Annotated[int, Path()]) -> Category:
    category = await Category.find_first_by_id(category_id)
    if category is None:
        raise CategoriesResponses.CATEGORY_NOT_FOUND
    return category


CategoryByIdDependency = Depends(get_category_by_id)
CategoryById = Annotated[Category, CategoryByIdDependency]
