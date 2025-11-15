from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.datalake_sch import DatalakeEventInputSchema
from app.datalake.models.datalake_events_db import DatalakeEvent

router = RedisRouter()


@router.subscriber(  # type: ignore[misc]  # bad typing in faststream
    stream=build_stream_sub(
        stream_name=settings.datalake_events_record_stream_name,
        service_name="datalake-service",
    ),
)
async def record_datalake_event(data: DatalakeEventInputSchema) -> None:
    await DatalakeEvent.create(**data.model_dump())
