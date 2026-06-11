from sqlalchemy import BigInteger, Integer, String, Enum, Float, Boolean, ForeignKey, DateTime, Date, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from core.db import Base

class SessionStatus(str, enum.Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"

class DifficultyModifier(str, enum.Enum):
    light = "light"
    normal = "normal"
    hard = "hard"

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    plan_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("workout_plans.id"))
    scheduled_date: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.planned)
    difficulty_modifier: Mapped[DifficultyModifier] = mapped_column(Enum(DifficultyModifier), default=DifficultyModifier.normal)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    duration_min: Mapped[int | None] = mapped_column(Integer)
    total_volume_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    calories_burned: Mapped[int | None] = mapped_column(Integer)
    xp_earned: Mapped[int | None] = mapped_column(Integer)
    rpe_session: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    structure: Mapped[str] = mapped_column(String(32))
    split_type: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SessionExercise(Base):
    __tablename__ = "session_exercises"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("workout_sessions.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exercises.id"))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    target_sets: Mapped[int] = mapped_column(Integer, default=3)
    target_reps: Mapped[int] = mapped_column(Integer, default=10)
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    rest_seconds: Mapped[int] = mapped_column(Integer, default=90)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

class ExerciseSet(Base):
    __tablename__ = "exercise_sets"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("session_exercises.id"), index=True)
    set_number: Mapped[int] = mapped_column(Integer)
    reps_done: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    rpe: Mapped[int | None] = mapped_column(Integer)
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
