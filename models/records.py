from sqlalchemy import BigInteger, Numeric, String, ForeignKey, DateTime, Date, Enum, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
import enum
from core.db import Base


class RecordType(str, enum.Enum):
    max_weight = "max_weight"
    max_reps = "max_reps"
    max_volume = "max_volume"
    estimated_1rm = "estimated_1rm"


class PersonalRecord(Base):
    __tablename__ = "personal_records"
    __table_args__ = (UniqueConstraint("user_id", "exercise_id", "record_type"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exercises.id"))
    record_type: Mapped[RecordType] = mapped_column(Enum(RecordType))
    value: Mapped[float] = mapped_column(Numeric(10, 2))
    achieved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
