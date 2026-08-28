from sqlalchemy import BigInteger, Integer, String, Enum, Boolean, Time, ForeignKey, JSON, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from core.db import Base


class ScheduleMode(str, enum.Enum):
    fixed = "fixed"
    spontaneous = "spontaneous"


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    mode: Mapped[ScheduleMode] = mapped_column(Enum(ScheduleMode), default=ScheduleMode.spontaneous)
    days_of_week: Mapped[list | None] = mapped_column(JSON, default=None)  # 1=Mon..7=Sun
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_time: Mapped[Time | None] = mapped_column(Time)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
