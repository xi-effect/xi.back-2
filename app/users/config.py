from pydantic import AwareDatetime, BaseModel

from app.common.config import settings
from app.common.itsdangerous_ext import SignedTokenProvider


class EmailConfirmationTokenPayloadSchema(BaseModel):
    user_id: int


email_confirmation_token_provider = SignedTokenProvider[
    EmailConfirmationTokenPayloadSchema
](
    secret_keys=settings.email_confirmation_keys.keys,
    encryption_ttl=settings.email_confirmation_keys.encryption_ttl,
    payload_schema=EmailConfirmationTokenPayloadSchema,
)


class EmailChangeTokenPayloadSchema(BaseModel):
    user_id: int
    new_email: str


email_change_token_provider = SignedTokenProvider[EmailChangeTokenPayloadSchema](
    secret_keys=settings.email_confirmation_keys.keys,
    encryption_ttl=settings.email_confirmation_keys.encryption_ttl,
    payload_schema=EmailChangeTokenPayloadSchema,
)


class PasswordResetTokenPayloadSchema(BaseModel):
    user_id: int
    password_last_changed_at: AwareDatetime


password_reset_token_provider = SignedTokenProvider[PasswordResetTokenPayloadSchema](
    secret_keys=settings.password_reset_keys.keys,
    encryption_ttl=settings.password_reset_keys.encryption_ttl,
    payload_schema=PasswordResetTokenPayloadSchema,
)
