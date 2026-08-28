from sqlalchemy import BigInteger, Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base


class CalibrationAnswer(Base):
    __tablename__ = "calibration_answers"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    question_key: Mapped[str] = mapped_column(String(64))
    answer: Mapped[dict] = mapped_column(JSON)
    answered_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
