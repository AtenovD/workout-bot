from sqlalchemy import BigInteger, Integer, String, Enum, Float, Boolean, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from core.db import Base

class EquipmentCategory(str, enum.Enum):
    none = "none"
    portable = "portable"
    stationary = "stationary"

class ExerciseType(str, enum.Enum):
    compound = "compound"
    isolation = "isolation"
    cardio = "cardio"
    mobility = "mobility"

class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    category: Mapped[EquipmentCategory] = mapped_column(Enum(EquipmentCategory))
    icon: Mapped[str | None] = mapped_column(String(8))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(String(512))

class MuscleGroup(Base):
    __tablename__ = "muscle_groups"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    body_part: Mapped[str] = mapped_column(String(32))

class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(String(1024))
    instructions: Mapped[list | None] = mapped_column(JSON)
    tips: Mapped[list | None] = mapped_column(JSON)
    common_mistakes: Mapped[list | None] = mapped_column(JSON)
    primary_muscle_group_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("muscle_groups.id"))
    required_equipment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("equipment.id"))
    equipment_category: Mapped[EquipmentCategory] = mapped_column(Enum(EquipmentCategory), default=EquipmentCategory.none)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType), default=ExerciseType.compound)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    met_value: Mapped[float | None] = mapped_column(Float)
    photo_url: Mapped[str | None] = mapped_column(String(512))
    video_url: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
