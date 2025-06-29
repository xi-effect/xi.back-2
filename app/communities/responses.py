from starlette import status

from app.common.fastapi_ext import Responses


class MoveResponses(Responses):
    INVALID_MOVE = status.HTTP_409_CONFLICT, "Invalid move"
