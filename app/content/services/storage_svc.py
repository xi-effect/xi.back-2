from starlette import status

from app.common.config_bdg import subscriptions_bridge
from app.common.fastapi_ext import Responses
from app.content.models.files_db import File
from app.content.models.ydocs_db import YDoc


async def compute_storage_usage_by_owner_id(owner_id: int) -> int:
    total_file_bytes = await File.sum_by_kwargs(File.size_bytes, owner_id=owner_id)
    total_ydoc_bytes = await YDoc.sum_by_kwargs(YDoc.size_bytes, owner_id=owner_id)
    return total_file_bytes + total_ydoc_bytes


async def has_owner_reached_storage_limit(owner_id: int) -> bool:
    plan = await subscriptions_bridge.retrieve_user_plan(user_id=owner_id)
    storage_usage = await compute_storage_usage_by_owner_id(owner_id=owner_id)
    return storage_usage >= plan.max_total_storage_bytes


class StorageLimitResponses(Responses):
    STORAGE_LIMIT_REACHED = status.HTTP_409_CONFLICT, "Storage limit reached"


async def ensure_owner_is_under_storage_limit(owner_id: int) -> None:
    if await has_owner_reached_storage_limit(owner_id=owner_id):
        raise StorageLimitResponses.STORAGE_LIMIT_REACHED
