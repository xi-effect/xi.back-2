from typing import Annotated

from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.categories_db import Category

category_not_found = EventException(404, "Category not found")


@register_dependency(exceptions=[category_not_found])
async def category_by_ids_dependency(
    category_id: int,
    community: CommunityById,
) -> Category:
    category = await Category.find_first_by_id(category_id)
    if category is None or category.community_id != community.id:
        raise category_not_found
    return category


CategoryByIds = Annotated[Category, category_by_ids_dependency]
