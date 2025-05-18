from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, ClassVar, Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, ForeignKey, Index, delete, select, update
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.users.models.users_db import User

session_token_generator = TokenGenerator(randomness=40, length=50)


class Session(Base):
    __tablename__ = "sessions"
    not_found_text: ClassVar[str] = "Session not found"

    expiry_timeout: ClassVar[timedelta] = timedelta(days=7)
    renew_period_length: ClassVar[timedelta] = timedelta(days=3)

    max_concurrent_sessions: ClassVar[int] = 10
    max_history_sessions: ClassVar[int] = 20
    max_history_timedelta: ClassVar[timedelta] = timedelta(days=7)

    @staticmethod
    def generate_expiry() -> AwareDatetime:
        return datetime_utc_now() + Session.expiry_timeout

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    user: Mapped[User] = relationship(passive_deletes=True)

    # Security
    token: Mapped[str] = mapped_column(CHAR(session_token_generator.token_length))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=generate_expiry
    )
    is_disabled: Mapped[bool] = mapped_column(default=False)

    @property
    def is_invalid(self) -> bool:  # noqa: FNE005
        return self.is_disabled or self.expires_at < datetime_utc_now()

    # User info
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    is_cross_site: Mapped[bool] = mapped_column(default=False)

    # Admin
    is_mub: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index("hash_index_session_token", token, postgresql_using="hash"),
    )

    FullSchema = MappedModel.create(
        columns=[
            id,
            (created_at, AwareDatetime),
            (expires_at, AwareDatetime),
            is_disabled,
        ],
        properties=[is_invalid],
    )
    MUBFullSchema = FullSchema.extend(columns=[is_mub])

    def is_renewal_required(self) -> bool:
        return self.expires_at - self.renew_period_length < datetime_utc_now()

    def renew(self) -> None:
        self.token = session_token_generator.generate_token()
        self.expires_at = self.generate_expiry()

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("token") is None:
            token = session_token_generator.generate_token()
            if (await Session.find_first_by_kwargs(token=token)) is not None:
                raise RuntimeError("Token collision happened (!wow!)")
            kwargs["token"] = token
        return await super().create(**kwargs)

    @classmethod
    async def find_by_user(
        cls,
        user_id: int,
        exclude_id: int | None = None,
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .filter_by(user_id=user_id, is_mub=False)
            .order_by(cls.expires_at.desc())
        )
        if exclude_id is not None:
            stmt = stmt.filter(cls.id != exclude_id)
        return await db.get_all(stmt)

    async def disable_all_other(self) -> None:
        await db.session.execute(
            update(type(self))
            .where(
                type(self).id != self.id,
                type(self).is_mub.is_(False),
                type(self).user_id == self.user_id,
                type(self).is_disabled.is_(False),
            )
            .values(is_disabled=True)
        )

    @classmethod
    async def cleanup_concurrent_by_user(cls, user_id: int) -> None:
        """Disable sessions above :py:attr:`max_concurrent_sessions`"""
        first_outside_limit: Self | None = await db.get_first(
            select(cls)
            .filter(cls.is_disabled.is_(False), cls.expires_at >= datetime_utc_now())
            .filter_by(user_id=user_id, is_mub=False)
            .order_by(cls.expires_at.desc())
            .offset(cls.max_concurrent_sessions)
        )
        if first_outside_limit is not None:
            await db.session.execute(
                update(cls)
                .where(
                    cls.user_id == user_id,
                    cls.is_mub.is_(False),
                    cls.expires_at <= first_outside_limit.expires_at,
                    cls.is_disabled.is_(False),
                )
                .values(is_disabled=True)
            )

    @classmethod
    async def cleanup_history_by_user(cls, user_id: int) -> None:
        """
        Delete sessions for the list of invalid ones, which are
        above :py:attr:`max_history_sessions` by number in the list
        or expired more than :py:attr:`max_history_timedelta` ago
        """

        max_outside_timestamp = datetime_utc_now() - cls.max_history_timedelta
        outside_limit: datetime = (
            await db.get_first(
                select(cls.expires_at)
                .filter(
                    cls.expires_at > max_outside_timestamp
                )  # if greater, fallback to max
                .filter_by(user_id=user_id)
                .order_by(cls.expires_at.desc())
                .offset(cls.max_history_sessions)
            )
            or max_outside_timestamp
        )

        await db.session.execute(
            delete(cls).where(
                cls.user_id == user_id,
                cls.expires_at <= outside_limit,
            )
        )

    @classmethod
    async def cleanup_by_user(cls, user_id: int) -> None:
        await cls.cleanup_concurrent_by_user(user_id)
        await cls.cleanup_history_by_user(user_id)

    @classmethod
    async def find_active_mub_session(cls, user_id: int) -> Self | None:
        return await db.get_first(
            select(cls)
            .filter(cls.is_disabled.is_(False), cls.expires_at > datetime_utc_now())
            .filter_by(user_id=user_id)
            .order_by(cls.expires_at.desc())
        )
