from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Annotated, ClassVar

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, AwareDatetime, StringConstraints
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base, settings
from app.common.cyptography import TokenGenerator
from app.common.utils.datetime import datetime_utc_now

password_reset_token_generator = TokenGenerator(randomness=40, length=50)


class OnboardingStage(StrEnum):
    CREATED = "created"
    COMMUNITY_CHOICE = "community-choice"
    COMMUNITY_CREATE = "community-create"
    COMMUNITY_INVITE = "community-invite"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    not_found_text: ClassVar[str] = "User not found"
    email_confirmation_resend_timeout: ClassVar[timedelta] = timedelta(minutes=10)

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(30))
    onboarding_stage: Mapped[OnboardingStage] = mapped_column(
        Enum(OnboardingStage, name="onboarding_stage"), default=OnboardingStage.CREATED
    )
    default_layout: Mapped[str | None] = mapped_column(String(10), default=None)
    theme: Mapped[str] = mapped_column(String(10), default="system")

    reset_token: Mapped[str | None] = mapped_column(
        CHAR(password_reset_token_generator.token_length)
    )
    last_password_change: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    email_confirmed: Mapped[bool] = mapped_column(default=False)
    allowed_confirmation_resend: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
        Index("hash_index_users_token", reset_token, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str,
        StringConstraints(min_length=6, max_length=100),
        AfterValidator(generate_hash),
    ]
    DisplayNameRequiredType = Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=30),
    ]
    DisplayNameType = DisplayNameRequiredType | None
    UsernameType = Annotated[str, StringConstraints(pattern="^[a-z0-9_.]{4,30}$")]

    EmailSchema = MappedModel.create(
        columns=[email]
    )  # TODO (email, Annotated[str, AfterValidator(email_validator)]),
    InputSchema = EmailSchema.extend(
        columns=[
            (username, UsernameType),
            (password, PasswordType),
        ]
    )
    PasswordSchema = MappedModel.create(columns=[password])
    CredentialsSchema = MappedModel.create(columns=[email, password])
    UserProfileSchema = MappedModel.create(columns=[id, username, display_name])
    SettingsSchema = MappedModel.create(
        columns=[
            (username, UsernameType),
            (display_name, DisplayNameType),
            default_layout,
            theme,
        ]
    )
    SettingsPatchSchema = SettingsSchema.as_patch()
    FullSchema = SettingsSchema.extend(
        columns=[
            id,
            email,
            email_confirmed,
            (last_password_change, AwareDatetime),
            (allowed_confirmation_resend, AwareDatetime),
            onboarding_stage,
        ]
    )
    FullPatchSchema = InputSchema.extend(
        columns=[(display_name, DisplayNameType), theme, onboarding_stage]
    ).as_patch()

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)

    def is_email_confirmation_resend_allowed(self) -> bool:
        return self.allowed_confirmation_resend < datetime_utc_now()

    def set_confirmation_resend_timeout(self) -> None:
        self.allowed_confirmation_resend = (
            datetime_utc_now() + self.email_confirmation_resend_timeout
        )

    @property
    def avatar_path(self) -> Path:
        return settings.avatars_path / f"{self.id}.webp"

    @property
    def generated_reset_token(self) -> str:  # noqa: FNE002  # reset is a noun here
        if self.reset_token is None:
            self.reset_token = password_reset_token_generator.generate_token()
        return self.reset_token

    def change_password(self, password: str) -> None:
        if not self.is_password_valid(password):
            self.last_password_change = datetime_utc_now()
        self.password = self.generate_hash(password)

    def reset_password(self, password: str) -> None:
        self.change_password(password)
        self.reset_token = None
