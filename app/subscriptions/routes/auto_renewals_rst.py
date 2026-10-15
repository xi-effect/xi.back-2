from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.subscriptions.dependencies.auto_renewals_dep import MyAutoRenewal

router = APIRouterExt(tags=["auto renewals"])


@router.delete(
    path="/users/current/auto-renewal/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel auto-renewal for the current user",
)
async def cancel_auto_renewal(auto_renewal: MyAutoRenewal) -> None:
    await auto_renewal.delete()
