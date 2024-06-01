from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import TypedDict

from pydantic import BaseModel

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community


class ChannelCategoryListItemSchema(BaseModel):
    category: Category.ResponseSchema | None
    channels: list[Channel.ResponseSchema]


class ChannelCategoryListItemDict(TypedDict):
    category: Category | None
    channels: list[Channel]


def collect_channels_and_categories_list(
    categories: Sequence[Category],
    category_id_to_channels: dict[None | int, list[Channel]],
) -> Iterable[ChannelCategoryListItemDict]:
    yield {
        "category": None,
        "channels": category_id_to_channels[None],
    }
    for category in categories:  # noqa: WPS526  # yield from messes with mypy
        yield {
            "category": category,
            "channels": category_id_to_channels[category.id],
        }


async def build_channels_and_categories_list(
    community: Community,
) -> list[ChannelCategoryListItemDict]:
    categories = await Category.find_all_by_community_id(community_id=community.id)
    channels = await Channel.find_all_by_community_id(community_id=community.id)

    category_id_to_channels: dict[None | int, list[Channel]] = defaultdict(list)
    for channel in channels:
        category_id_to_channels[channel.category_id].append(channel)

    return list(
        collect_channels_and_categories_list(categories, category_id_to_channels)
    )
