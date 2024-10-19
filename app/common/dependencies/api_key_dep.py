from typing import Annotated, Final

from fastapi import Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from app.common.config import settings
from app.common.fastapi_ext import Responses, with_responses

API_KEY_HEADER_NAME: Final[str] = "X-Api-Key"

header_mub_scheme = APIKeyHeader(
    name=API_KEY_HEADER_NAME, auto_error=False, scheme_name="api key header"
)
KeyHeader = Annotated[str | None, Depends(header_mub_scheme)]


class APIKeyResponses(Responses):
    INVALID_API_KEY = (HTTP_401_UNAUTHORIZED, "Invalid key")


@with_responses(APIKeyResponses)
def api_key_verification(api_key: KeyHeader = None) -> None:
    if api_key != settings.api_key:
        raise APIKeyResponses.INVALID_API_KEY.value


APIKeyProtection = Depends(api_key_verification)
