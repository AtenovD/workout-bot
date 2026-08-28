from sqlalchemy import Column, BigInteger, Integer, ForeignKey, Numeric, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from core.db import Base


class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(BigInteger, ForeignKey("exercises.id"), nullable=False)
    record_type = Column(String(16), nullable=False)  # max_weight, max_reps, max_volume, estimated_1rm
    value = Column(Numeric(10, 2), nullable=False)
    achieved_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", "record_type"),
    )
