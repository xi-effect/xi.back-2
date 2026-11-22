from pydantic import AwareDatetime, BaseModel


class UserProfileSchema(BaseModel):
    display_name: str


class UserProfileWithIDSchema(UserProfileSchema):
    user_id: int


class DetailedUserSchema(UserProfileSchema):
    email: str
    created_at: AwareDatetime
