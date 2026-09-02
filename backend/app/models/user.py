from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", server_default="active")

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )
    resume: Mapped["Resume | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
    )


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    real_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    school: Mapped[str | None] = mapped_column(String(100), nullable=True)
    major: Mapped[str | None] = mapped_column(String(100), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(30), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    career_direction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    desired_cities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    job_type: Mapped[str | None] = mapped_column(String(30), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
