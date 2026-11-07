from typing import Annotated

from fastapi import Depends
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.subscriptions.models.auto_renewals_db import AutoRenewal


class AutoRenewalResponses(Responses):
    AUTO_RENEWAL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Auto-renewal not found"


@with_responses(AutoRenewalResponses)
async def get_my_auto_renewal(auth_data: AuthorizationData) -> AutoRenewal:
    auto_renewal = await AutoRenewal.find_first_by_id(auth_data.user_id)
    if auto_renewal is None:
        raise AutoRenewalResponses.AUTO_RENEWAL_NOT_FOUND
    return auto_renewal


MyAutoRenewal = Annotated[AutoRenewal, Depends(get_my_auto_renewal)]
