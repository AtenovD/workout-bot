"""
Gamification service — XP calculation, levels, and achievements.
"""
from dataclasses import dataclass


XP_PER_LEVEL = [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700, 3250]
# After level 10: each level needs 600 more XP than the previous

MODIFIER_XP_BONUS = {
    "light":  0.8,
    "normal": 1.0,
    "hard":   1.3,
}

TITLES = {
    1:  "Новичок",
    3:  "Любитель",
    5:  "Тренирующийся",
    7:  "Спортсмен",
    10: "Атлет",
    13: "Мастер",
    16: "Эксперт",
    20: "Зверь",
    25: "Легенда",
    30: "Бог зала",
}


@dataclass
class XPResult:
    xp_earned: int
    breakdown: dict[str, int]


def get_level_from_xp(total_xp: int) -> int:
    """Get level number from total XP."""
    if total_xp <= 0:
        return 1
    level = 1
    cumulative = 0
    for i, threshold in enumerate(XP_PER_LEVEL):
        cumulative += threshold
        if total_xp >= cumulative:
            level = i + 1
        else:
            break
    # After pre-defined levels
    if level >= len(XP_PER_LEVEL):
        base_xp = sum(XP_PER_LEVEL)
        extra_xp = total_xp - base_xp
        extra_level = extra_xp // (600 + (level - len(XP_PER_LEVEL)) * 50)
        level += extra_level
    return max(1, level)


def get_xp_for_next_level(current_level: int, total_xp: int) -> tuple[int, int]:
    """Returns (xp_needed_for_next_level, xp_progress_in_current_level)."""
    if current_level < len(XP_PER_LEVEL):
        threshold = XP_PER_LEVEL[current_level]
    else:
        threshold = 600 + (current_level - len(XP_PER_LEVEL)) * 50
    prev_total = sum(XP_PER_LEVEL[:current_level]) if current_level < len(XP_PER_LEVEL) else (
        sum(XP_PER_LEVEL) + sum(600 + i * 50 for i in range(current_level - len(XP_PER_LEVEL)))
    )
    progress = total_xp - prev_total
    return threshold, max(0, progress)


def get_title(level: int) -> str:
    """Get the user's title for their level."""
    title = "Новичок"
    for lvl, t in sorted(TITLES.items()):
        if level >= lvl:
            title = t
    return title


def calculate_xp(
    total_volume_kg: float,
    difficulty_modifier: str = "normal",
    streak: int = 0,
    pr_count: int = 0,
    was_skipped_before: bool = False,
) -> XPResult:
    """
    Calculate XP earned for completing a workout.
    
    Base XP: 50
    Volume bonus: 1 XP per 100 kg
    Modifier bonus: multiplier
    Streak bonus: 2 XP per day streak (max 50)
    PR bonus: 15 XP per PR
    Comeback bonus: 25 XP if returning after skip
    """
    base = 50
    volume_bonus = int(total_volume_kg / 100)
    modifier_mult = MODIFIER_XP_BONUS.get(difficulty_modifier, 1.0)
    streak_bonus = min(50, streak * 2)
    pr_bonus = pr_count * 15
    comeback_bonus = 25 if was_skipped_before else 0

    total = int((base + volume_bonus + streak_bonus + pr_bonus + comeback_bonus) * modifier_mult)
    
    return XPResult(
        xp_earned=max(10, total),
        breakdown={
            "base": base,
            "volume": volume_bonus,
            "streak": streak_bonus,
            "pr": pr_bonus,
            "comeback": comeback_bonus,
            "modifier": f"x{modifier_mult}",
        }
    )
