from collections.abc import Sequence
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Self

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from pydantic import AfterValidator, AwareDatetime, StringConstraints
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, Index, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base, settings
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

password_reset_token_generator = TokenGenerator(randomness=40, length=50)


class OnboardingStage(StrEnum):
    EMAIL_CONFIRMATION = "email-confirmation"
    USER_INFORMATION = "user-information"
    DEFAULT_LAYOUT = "default-layout"
    NOTIFICATIONS = "notifications"
    TRAINING = "training"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    @staticmethod
    def generate_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    @staticmethod
    def generate_next_email_confirmation_allowed_resend_at() -> datetime:
        return datetime_utc_now() + timedelta(minutes=10)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(
        String(30),
        default=lambda context: context.get_current_parameters()["username"],
    )

    default_layout: Mapped[str | None] = mapped_column(String(10), default=None)
    theme: Mapped[str] = mapped_column(String(10), default="system")

    onboarding_stage: Mapped[OnboardingStage] = mapped_column(
        Enum(OnboardingStage, name="onboarding_stage_3"),
        default=OnboardingStage.EMAIL_CONFIRMATION,
    )

    email_confirmation_resend_allowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime_utc_now,
    )

    password_last_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime_utc_now,
    )

    __table_args__ = (
        Index("hash_index_users_username", username, postgresql_using="hash"),
        Index("hash_index_users_email", email, postgresql_using="hash"),
    )

    PasswordType = Annotated[
        str,
        StringConstraints(min_length=6, max_length=100),
        AfterValidator(generate_hash),
    ]
    DisplayNameType = Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=30),
    ]
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
            (password_last_changed_at, AwareDatetime),
            (email_confirmation_resend_allowed_at, AwareDatetime),
            onboarding_stage,
        ]
    )
    PatchMUBSchema = InputSchema.extend(
        columns=[(display_name, DisplayNameType), theme, onboarding_stage]
    ).as_patch()

    @classmethod
    async def find_all_by_ids(cls, user_ids: list[int]) -> Sequence[Self]:
        return await db.get_all(select(cls).filter(cls.id.in_(user_ids)))

    def is_password_valid(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password)

    def is_email_confirmation_resend_allowed(self) -> bool:
        return self.email_confirmation_resend_allowed_at < datetime_utc_now()

    def timeout_email_confirmation_resend(self) -> None:
        self.email_confirmation_resend_allowed_at = (
            self.generate_next_email_confirmation_allowed_resend_at()
        )

    @property
    def avatar_path(self) -> Path:
        return settings.avatars_path / f"{self.id}.webp"

    def change_password(self, password: str) -> None:
        if self.is_password_valid(password):
            return
        self.password_last_changed_at = datetime_utc_now()
        self.password = self.generate_hash(password)
