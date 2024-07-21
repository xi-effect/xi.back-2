from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel
from tmexio import Emitter, EventException, PydanticPackager

from app.common.abscract_models.ordered_lists_db import InvalidMoveException
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.categories_sio_dep import CategoryByIds
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    current_owner_dependency,
    current_participant_dependency,
)
from app.communities.models.categories_db import Category
from app.communities.rooms import community_room

router = EventRouterExt(tags=["categories-list"])


@router.on("list-categories", dependencies=[current_participant_dependency])
async def list_categories(
    community: CommunityById,
) -> Annotated[Sequence[Category], PydanticPackager(list[Category.ResponseSchema])]:
    return await Category.find_all_by_community_id(community_id=community.id)


quantity_limit_exceeded = EventException(409, "Quantity limit exceeded")


class CategoryServerSchema(BaseModel):
    community_id: int
    category: Category.ResponseSchema


class CategoryPreSchema(BaseModel):
    community_id: int
    category: Category


@router.on(
    "create-category",
    exceptions=[quantity_limit_exceeded],
    dependencies=[current_owner_dependency],
)
async def create_category(
    community: CommunityById,
    data: Category.InputSchema,
    duplex_emitter: Annotated[Emitter[CategoryPreSchema], CategoryServerSchema],
) -> Annotated[Category, PydanticPackager(Category.ResponseSchema, code=201)]:
    if await Category.is_limit_per_community_reached(community_id=community.id):
        raise quantity_limit_exceeded

    category = await Category.create(community_id=community.id, **data.model_dump())
    await db.session.commit()

    await duplex_emitter.emit(
        CategoryPreSchema(community_id=category.community_id, category=category),
        target=community_room(category.community_id),
        exclude_self=True,
    )
    return category


@router.on("update-category", dependencies=[current_owner_dependency])
async def update_category(
    category: CategoryByIds,
    data: Category.PatchSchema,
    duplex_emitter: Annotated[Emitter[CategoryPreSchema], CategoryServerSchema],
) -> Annotated[Category, PydanticPackager(Category.ResponseSchema)]:
    category.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await duplex_emitter.emit(
        CategoryPreSchema(community_id=category.community_id, category=category),
        target=community_room(category.community_id),
        exclude_self=True,
    )
    return category


class CategoryIdsSchema(BaseModel):
    community_id: int
    category_id: int


class MoveCategoryServerSchema(CategoryIdsSchema):
    after_id: int | None
    before_id: int | None


invalid_move = EventException(409, "Invalid move")


@router.on(
    "move-category",
    exceptions=[invalid_move],
    dependencies=[current_owner_dependency],
)
async def move_category(
    category: CategoryByIds,
    after_id: int | None,
    before_id: int | None,
    duplex_emitter: Emitter[MoveCategoryServerSchema],
) -> None:
    try:
        await category.validate_and_move(
            list_id=category.list_id,
            after_id=after_id,
            before_id=before_id,
        )
    except InvalidMoveException as e:
        # TODO warns as if the exception is not documented
        raise EventException(409, e.message)

    await db.session.commit()

    await duplex_emitter.emit(
        MoveCategoryServerSchema(
            community_id=category.community_id,
            category_id=category.id,
            after_id=after_id,
            before_id=before_id,
        ),
        target=community_room(category.community_id),
        exclude_self=True,
    )


@router.on("delete-category", dependencies=[current_owner_dependency])
async def delete_category(
    category: CategoryByIds,
    duplex_emitter: Emitter[CategoryIdsSchema],
) -> None:
    await category.delete()
    await db.session.commit()

    await duplex_emitter.emit(
        CategoryIdsSchema(community_id=category.community_id, category_id=category.id),
        target=community_room(category.community_id),
        exclude_self=True,
    )
