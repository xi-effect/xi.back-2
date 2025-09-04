from app.autocomplete.dependencies.subjects_dep import SubjectByID
from app.autocomplete.models.subjects_db import Subject
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.autocomplete_sch import SubjectSchema

router = APIRouterExt(tags=["subjects internal"])


@router.get(
    "/subjects/{subject_id}/",
    response_model=SubjectSchema,
    summary="Retrieve any subject by id",
)
async def retrieve_subject(subject: SubjectByID) -> Subject:
    return subject
