"""
Gamification service: XP, levels, streaks, achievements.
"""
import math
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class XPResult:
    xp_earned: int
    new_total_xp: int
    new_level: int
    leveled_up: bool
    breakdown: dict


LEVEL_TITLES = {
    1: "Новичок",
    5: "Любитель",
    10: "Атлет",
    20: "Зверь",
    35: "Машина",
    50: "Легенда",
}


def xp_for_level(level: int) -> int:
    """XP needed to reach this level."""
    return round(100 * (level ** 1.5))


def get_level_from_xp(total_xp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def get_title(level: int) -> str:
    """Get title for level."""
    title = "Новичок"
    for lvl, t in sorted(LEVEL_TITLES.items()):
        if level >= lvl:
            title = t
    return title


def calculate_xp(
    total_volume_kg: float,
    difficulty_modifier: str,
    streak: int,
    pr_count: int,
    was_skipped_before: bool,
) -> XPResult:
    base = 50
    volume_bonus = min(round(total_volume_kg / 100), 50)
    difficulty_bonus = {"light": 0, "normal": 10, "hard": 25}.get(difficulty_modifier, 10)
    streak_multiplier = min(1.0 + streak * 0.05, 2.0)
    pr_bonus = pr_count * 20
    skip_penalty = -15 if was_skipped_before else 0

    xp = round((base + volume_bonus + difficulty_bonus + pr_bonus + skip_penalty) * streak_multiplier)
    xp = max(xp, 10)

    return XPResult(
        xp_earned=xp,
        new_total_xp=0,  # to be filled by caller
        new_level=0,
        leveled_up=False,
        breakdown={
            "base": base,
            "volume": volume_bonus,
            "difficulty": difficulty_bonus,
            "streak": f"x{streak_multiplier:.1f}",
            "pr": pr_bonus,
            "penalty": skip_penalty,
        },
    )


def check_streak(last_workout_date: Optional[date], today: date, schedule_days: list[int]) -> tuple[int, bool]:
    """Returns (new_streak, streak_broken)."""
    if last_workout_date is None:
        return 1, False
    delta = (today - last_workout_date).days
    if delta <= 1:
        return 1, False  # streak continues (to be incremented by caller)
    return 0, True  # streak broken
