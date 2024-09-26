from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.task_channels_db import TaskChannel


class TaskChannelResponses(Responses):
    TASK_CHANNEL_NOT_FOUND = 404, "Task-channel not found"


@with_responses(TaskChannelResponses)
async def get_task_channel_by_id(channel_id: Annotated[int, Path()]) -> TaskChannel:
    task_channel = await TaskChannel.find_first_by_id(channel_id)
    if task_channel is None:
        raise TaskChannelResponses.TASK_CHANNEL_NOT_FOUND
    return task_channel


TaskChannelById = Annotated[TaskChannel, Depends(get_task_channel_by_id)]
