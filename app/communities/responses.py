from app.common.fastapi_ext import Responses


class MoveResponses(Responses):
    INVALID_MOVE = 409, "Invalid move"
