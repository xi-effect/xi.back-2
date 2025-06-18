from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.tasks_db import Task


class TaskResponses(Responses):
    TASK_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Task not found"


@with_responses(TaskResponses)
async def get_task_by_id(task_id: Annotated[int, Path()]) -> Task:
    task = await Task.find_first_by_id(task_id)
    if task is None:
        raise TaskResponses.TASK_NOT_FOUND
    return task


TaskById = Annotated[Task, Depends(get_task_by_id)]
