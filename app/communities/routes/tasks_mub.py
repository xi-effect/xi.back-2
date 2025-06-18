from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.task_channels_dep import TaskChannelById
from app.communities.dependencies.tasks_dep import TaskById
from app.communities.models.tasks_db import Task, TaskKind, TaskOrderingType

router = APIRouterExt(tags=["tasks mub"])


@router.get(
    "/task-channels/{channel_id}/tasks/",
    response_model=list[Task.ResponseSchema],
    summary="List paginated tasks in a channel",
)
async def list_tasks(
    task_channel: TaskChannelById,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    is_only_active: bool = False,
    ordering_type: TaskOrderingType = TaskOrderingType.CREATED_AT,
    kind: TaskKind | None = None,
) -> Sequence[Task]:
    return await Task.find_paginated_by_filter(
        task_channel.id, offset, limit, is_only_active, ordering_type, kind
    )


@router.post(
    "/task-channels/{channel_id}/tasks/",
    status_code=status.HTTP_201_CREATED,
    response_model=Task.ResponseSchema,
    summary="Create a new task in a channel",
)
async def create_task(task_channel: TaskChannelById, data: Task.InputSchema) -> Task:
    return await Task.create(channel_id=task_channel.id, **data.model_dump())


@router.get(
    "/tasks/{task_id}/",
    response_model=Task.ResponseSchema,
    summary="Retrieve any task by id",
)
async def retrieve_task(task: TaskById) -> Task:
    return task


@router.patch(
    "/tasks/{task_id}/",
    response_model=Task.ResponseSchema,
    summary="Update any task by id",
)
async def patch_task(task: TaskById, data: Task.PatchSchema) -> Task:
    task.update(**data.model_dump(exclude_defaults=True))
    return task


@router.delete(
    "/tasks/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any task by id",
)
async def delete_task(task: TaskById) -> None:
    await task.delete()
