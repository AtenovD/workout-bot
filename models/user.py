from sqlalchemy import Integer, BigInteger, String, Enum, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from core.db import Base

class UserStatus(str, enum.Enum):
    active = "active"
    banned = "banned"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    language_code: Mapped[str | None] = mapped_column(String(8), default="ru")
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    stats: Mapped["UserStats"] = relationship("UserStats", back_populates="user", uselist=False)
