from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.models.communities_db import Community

router = APIRouterExt(tags=["communities meta mub"])


@router.post(
    "/communities/",
    status_code=201,
    response_model=Community.FullResponseSchema,
    summary="Create a new community",
)
async def create_community(data: Community.FullInputSchema) -> Community:
    return await Community.create(**data.model_dump())


@router.get(
    "/communities/{community_id}/",
    response_model=Community.FullResponseSchema,
    summary="Retrieve any community by id",
)
async def retrieve_community(community: CommunityById) -> Community:
    return community


@router.patch(
    "/communities/{community_id}/",
    response_model=Community.FullResponseSchema,
    summary="Update any community by id",
)
async def patch_community(
    community: CommunityById, data: Community.FullPatchSchema
) -> Community:
    community.update(**data.model_dump(exclude_defaults=True))
    return community


@router.delete(
    "/communities/{community_id}/",
    status_code=204,
    summary="Delete any community by id",
)
async def delete_community(community: CommunityById) -> None:
    await community.delete()
