from collections.abc import AsyncIterator

import pytest
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.task_channels_db import TaskChannel
from app.communities.models.tasks_db import Task, TaskKind, TaskOrderingType
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.communities import factories

pytestmark = pytest.mark.anyio

TASK_LIST_SIZE = 6


@pytest.fixture()
async def tasks_data(
    active_session: ActiveSession,
    task_channel: TaskChannel,
) -> AsyncIterator[list[tuple[Task, AnyJSON]]]:
    async with active_session():
        tasks = [
            await Task.create(
                channel_id=task_channel.id,
                **factories.TaskInputFactory.build().model_dump(),
            )
            for _ in range(TASK_LIST_SIZE)
        ]

    yield [
        (
            task,
            Task.ResponseSchema.model_validate(task, from_attributes=True).model_dump(
                mode="json"
            ),
        )
        for task in tasks
    ]

    async with active_session():
        for task in tasks:
            await task.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TASK_LIST_SIZE, id="start_to_end"),
        pytest.param(TASK_LIST_SIZE // 2, TASK_LIST_SIZE, id="middle_to_end"),
        pytest.param(0, TASK_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
@pytest.mark.parametrize(
    ("ordering_type", "order_by_field_name"),
    [
        pytest.param(
            TaskOrderingType.CREATED_AT, "created_at", id="created_at_ordering"
        ),
        pytest.param(
            TaskOrderingType.OPENING_AT, "opening_at", id="opening_at_ordering"
        ),
        pytest.param(
            TaskOrderingType.CLOSING_AT, "closing_at", id="closing_at_ordering"
        ),
    ],
)
@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(None, id="no_kind_filtering"),
        pytest.param(TaskKind.TASK, id="task_kind_filtering"),
        pytest.param(TaskKind.TEST, id="test_kind_filtering"),
    ],
)
@pytest.mark.parametrize(
    "is_only_active",
    [
        pytest.param(True, id="only_active_filtering"),
        pytest.param(False, id="no_only_active_filtering"),
    ],
)
@freeze_time()
async def test_tasks_listing(
    mub_client: TestClient,
    task_channel: TaskChannel,
    tasks_data: list[tuple[Task, AnyJSON]],
    offset: int,
    limit: int,
    ordering_type: TaskOrderingType,
    order_by_field_name: str,
    kind: TaskKind | None,
    is_only_active: bool | None,
) -> None:
    filtered_tasks_data = [
        (task, task_data)
        for task, task_data in tasks_data
        if (kind is None or task.kind == kind)
        and (not is_only_active or task.is_active)
    ]

    sorted_tasks_data = sorted(
        filtered_tasks_data,
        key=lambda task_tuple: getattr(task_tuple[0], order_by_field_name),
        reverse=True,
    )

    assert_response(
        mub_client.get(
            f"/mub/community-service/task-channels/{task_channel.id}/tasks/",
            params=remove_none_values(
                {
                    "offset": offset,
                    "limit": limit,
                    "ordering_type": ordering_type,
                    "kind": kind,
                    "is_only_active": is_only_active,
                }
            ),
        ),
        expected_json=[
            task_data for _, task_data in sorted_tasks_data[offset : offset + limit]
        ],
    )


async def test_tasks_listing_task_channel_not_found(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_task_channel_id: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/task-channels/{deleted_task_channel_id}/tasks/",
            params={"offset": 0, "limit": TASK_LIST_SIZE},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Task-channel not found"},
    )
