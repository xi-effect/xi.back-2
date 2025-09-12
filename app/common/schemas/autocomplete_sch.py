from pydantic import BaseModel


class SubjectSchema(BaseModel):
    id: int
    name: str
