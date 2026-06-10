from sqlalchemy import String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MapperEvents, relationship
from datetime import datetime
from typing import List


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String())
    email: Mapped[str] = mapped_column(String(), unique=True)
    hashed_password: Mapped[str] = mapped_column(String())
    is_active: Mapped[bool] = mapped_column(Boolean())

    session: Mapped["UserSession"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    role_name: Mapped[int] = mapped_column(ForeignKey("users_roles.id", ondelete="RESTRICT"))

    role: Mapped["UsersRoles"] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f'ID: {self.id}, email: {self.email}'


class UserSession(Base):
    __tablename__ = "user_session"
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    token_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    user: Mapped["User"] = relationship(back_populates="session")


class UsersRoles(Base):
    __tablename__ = "users_roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    name_role: Mapped[str] = mapped_column(String(32), unique=True)
    create: Mapped[bool] = mapped_column(Boolean(), default=False)
    read: Mapped[bool] = mapped_column(Boolean(), default=False)
    update: Mapped[bool] = mapped_column(Boolean(), default=False)
    delete: Mapped[bool] = mapped_column(Boolean(), default=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")


class Posts(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    heading: Mapped[str] = mapped_column(String(120))
    article: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
