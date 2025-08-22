from starlette import status

from app.common.fastapi_ext import Responses


class LimitedListResponses(Responses):
    QUANTITY_EXCEEDED = status.HTTP_409_CONFLICT, "Quantity exceeded"


class SelfReferenceResponses(Responses):
    TARGET_IS_THE_SOURCE = status.HTTP_409_CONFLICT, "Target is the source"
