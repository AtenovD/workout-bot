from sqlalchemy import Integer, BigInteger, Numeric, String, Enum, DateTime, Date, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from core.db import Base

class Gender(str, enum.Enum):
    male = "male"
    female = "female"

class Goal(str, enum.Enum):
    mass_gain = "mass_gain"
    maintenance = "maintenance"
    weight_loss = "weight_loss"
    cardio = "cardio"

class ExperienceLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class TrainingStructure(str, enum.Enum):
    fullbody = "fullbody"
    split = "split"

class SplitType(str, enum.Enum):
    upper_lower = "upper_lower"
    push_pull_legs = "push_pull_legs"
    bro_split = "bro_split"

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender))
    birth_date: Mapped[Date | None] = mapped_column(Date)
    height_cm: Mapped[int | None] = mapped_column(Integer)
    current_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    goal: Mapped[Goal | None] = mapped_column(Enum(Goal))
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(Enum(ExperienceLevel))
    training_experience_months: Mapped[int | None] = mapped_column(Integer, default=0)
    training_structure: Mapped[TrainingStructure | None] = mapped_column(Enum(TrainingStructure))
    split_type: Mapped[SplitType | None] = mapped_column(Enum(SplitType))
    intensity_level: Mapped[int | None] = mapped_column(Integer, default=3)
    preferred_duration_min: Mapped[int | None] = mapped_column(Integer, default=45)
    health_flags: Mapped[dict | None] = mapped_column(JSON, default=list)
    calibrated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="profile")
