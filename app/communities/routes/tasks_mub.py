from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.tasks_dep import TaskById
from app.communities.models.tasks_db import Task, TaskOrdering

router = APIRouterExt(tags=["tasks mub"])


@router.post(
    "/communities/{community_id}/tasks/",
    status_code=201,
    response_model=Task.ResponseSchema,
    summary="Create a new task",
)
async def create_task(community_id: int, data: Task.InputSchema) -> Task:
    return await Task.create(community_id=community_id, **data.model_dump())


@router.get(
    "/tasks/{task_id}/",
    status_code=200,
    response_model=Task.ResponseSchema,
    summary="Get task by id",
)
async def get_task(task: TaskById) -> Task:
    return task


@router.get(
    "/communities/{community_id}/tasks/paginated/",
    status_code=200,
    response_model=list[Task.ResponseSchema],
    summary="Get paginated tasks by task id",
)
async def get_paginated_tasks(
    community: CommunityById,
    offset: int,
    limit: int,
    is_only_active: bool,
    ordering: TaskOrdering,
) -> Sequence[Task]:
    return await Task.get_paginated(
        community.id,
        offset,
        limit,
        is_only_active,
        ordering,
    )


@router.get(
    "/communities/{community_id}/tasks/",
    status_code=200,
    response_model=list[Task.ResponseSchema],
    summary="Get all community tasks",
)
async def get_tasks(community_id: int) -> Sequence[Task]:
    return await Task.find_all_by_kwargs(community_id=community_id)


@router.patch(
    "/tasks/{task_id}/",
    status_code=200,
    response_model=Task.ResponseSchema,
    summary="Patch the task",
)
async def patch_task(task: TaskById, data: Task.PatchSchema) -> Task:
    task.update(**data.model_dump(exclude_defaults=True))
    return task


@router.delete(
    "/communities/{community_id}/tasks/{task_id}/",
    status_code=204,
    summary="Delete community task by id",
)
async def delete_task(task: TaskById) -> None:
    await task.delete()
