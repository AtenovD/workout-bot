from sqlalchemy import BigInteger, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
import enum
from core.db import Base


class AlternativeReason(str, enum.Enum):
    no_equipment = "no_equipment"
    easier = "easier"
    harder = "harder"
    disliked = "disliked"
    injury_safe = "injury_safe"


class ExerciseAlternative(Base):
    __tablename__ = "exercise_alternatives"
    __table_args__ = (UniqueConstraint("exercise_id", "alternative_exercise_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exercises.id"), index=True)
    alternative_exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exercises.id"))
    reason: Mapped[AlternativeReason] = mapped_column(Enum(AlternativeReason), default=AlternativeReason.no_equipment)
