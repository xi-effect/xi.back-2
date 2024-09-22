from typing import Any

import pytest
from starlette.testclient import TestClient

from app.communities.models.task_channels_db import TaskChannel
from app.communities.models.tasks_db import Task
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import TaskInputFactory, TaskPatchFactory

pytestmark = pytest.mark.anyio


async def test_task_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    task_channel: TaskChannel,
) -> None:
    task_input_data = TaskInputFactory.build_json()
    task_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/task-channels/{task_channel.id}/tasks/",
            json=task_input_data,
        ),
        expected_code=201,
        expected_json={
            **task_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        task = await Task.find_first_by_id(task_id)
        assert task is not None
        await task.delete()


async def test_task_creation_task_channel_not_found(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_task_channel_id: int,
) -> None:
    task_input_data = TaskInputFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/community-service/task-channels/{deleted_task_channel_id}/tasks/",
            json=task_input_data,
        ),
        expected_code=404,
        expected_json={"detail": "Task-channel not found"},
    )


async def test_task_retrieving(
    mub_client: TestClient,
    task: Task,
    task_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/tasks/{task.id}/"),
        expected_json=task_data,
    )


async def test_task_updating(
    mub_client: TestClient,
    task: Task,
    task_data: AnyJSON,
) -> None:
    task_patch_data = TaskPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/tasks/{task.id}/",
            json=task_patch_data,
        ),
        expected_json={**task_data, **task_patch_data},
    )


async def test_task_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    task: Task,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/tasks/{task.id}/"),
    )

    async with active_session():
        assert (await Task.find_first_by_id(task.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", TaskPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_task_not_finding(
    mub_client: TestClient,
    deleted_task_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/tasks/{deleted_task_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Task not found"},
    )
