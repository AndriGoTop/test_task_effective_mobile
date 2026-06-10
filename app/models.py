from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MapperEvents, relationship


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

    def __repr__(self) -> str:
        return f'ID: {self.id}, email: {self.email}'


class UserSession(Base):
    __tablename__ = "user_session"
    id: Mapped[int] = mapped_column(primary_key=True)


    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    token_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean(), default=True)

    user: Mapped["User"] = relationship(back_populates="session")
