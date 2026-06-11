from sqlalchemy import BigInteger, Integer, String, Enum, Float, Numeric, Date, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from core.db import Base

class AchievementCategory(str, enum.Enum):
    consistency = "consistency"
    strength = "strength"
    volume = "volume"
    milestone = "milestone"
    special = "special"

class AchievementTier(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"

class UserStats(Base):
    __tablename__ = "user_stats"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_workouts: Mapped[int] = mapped_column(Integer, default=0)
    total_volume_kg: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    last_workout_date: Mapped[Date | None] = mapped_column(Date)

class Achievement(Base):
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(512))
    icon: Mapped[str | None] = mapped_column(String(8))
    category: Mapped[AchievementCategory] = mapped_column(Enum(AchievementCategory))
    tier: Mapped[AchievementTier] = mapped_column(Enum(AchievementTier))
    condition: Mapped[dict] = mapped_column(JSON)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    achievement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("achievements.id"))
    unlocked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    progress: Mapped[float] = mapped_column(Float, default=0.0)
