from starlette import status

from app.common.config_bdg import datalake_bridge
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.datalake_sch import DatalakeEventInputSchema

router = APIRouterExt(tags=["datalake events mub"])


@router.post(
    path="/datalake-events/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Queue recording a datalake event",
)
async def queue_datalake_event_recording(data: DatalakeEventInputSchema) -> None:
    await datalake_bridge.record_datalake_event(data)
