from sqlalchemy import BigInteger, Integer, Date, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from core.db import Base


class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    challenge_code: Mapped[str] = mapped_column(String(32), nullable=False, default="30day")
    started_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    current_day: Mapped[int] = mapped_column(Integer, default=0)
    completed_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
