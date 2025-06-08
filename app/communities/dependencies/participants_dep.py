from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.participants_db import Participant


class ParticipantResponses(Responses):
    PARTICIPANT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Participant not found"


@with_responses(ParticipantResponses)
async def get_participant_by_id(participant_id: Annotated[int, Path()]) -> Participant:
    participant = await Participant.find_first_by_id(participant_id)
    if participant is None:
        raise ParticipantResponses.PARTICIPANT_NOT_FOUND
    return participant


ParticipantById = Annotated[Participant, Depends(get_participant_by_id)]
