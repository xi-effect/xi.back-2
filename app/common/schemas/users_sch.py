from pydantic import BaseModel


class UserProfileSchema(BaseModel):
    username: str
    display_name: str | None


class UserProfileWithIDSchema(UserProfileSchema):
    user_id: int
