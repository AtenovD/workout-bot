"""Longer-term training strategy for generated workouts."""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.profile import Goal, Profile, SplitType, TrainingStructure
from models.workout import SessionStatus, WorkoutPlan, WorkoutSession


DEFAULT_CYCLE_LENGTH_WEEKS = 6

PHASES = {
    1: {
        "code": "base",
        "title": "Неделя базы и техники",
        "volume_factor": 1.0,
        "intensity_factor": 0.96,
        "rest_factor": 1.05,
    },
    2: {
        "code": "progression",
        "title": "Неделя прогрессии",
        "volume_factor": 1.0,
        "intensity_factor": 1.0,
        "rest_factor": 1.0,
    },
    3: {
        "code": "progression",
        "title": "Неделя прогрессии",
        "volume_factor": 1.08,
        "intensity_factor": 1.03,
        "rest_factor": 1.0,
    },
    4: {
        "code": "volume",
        "title": "Объёмная неделя",
        "volume_factor": 1.18,
        "intensity_factor": 0.98,
        "rest_factor": 0.95,
    },
    5: {
        "code": "intensity",
        "title": "Интенсивная неделя",
        "volume_factor": 0.92,
        "intensity_factor": 1.08,
        "rest_factor": 1.12,
    },
    6: {
        "code": "deload",
        "title": "Разгрузочная неделя",
        "volume_factor": 0.72,
        "intensity_factor": 0.86,
        "rest_factor": 1.15,
    },
}


@dataclass(frozen=True)
class StrategyContext:
    plan: WorkoutPlan
    completed_count: int
    cycle_week: int
    session_index: int
    sessions_per_week: int
    phase_code: str
    phase_title: str
    focus_groups: list[str]
    volume_factor: float
    intensity_factor: float
    rest_factor: float

    @property
    def note(self) -> str:
        focus = ",".join(self.focus_groups)
        return (
            f"plan:{self.plan.id};week:{self.cycle_week};phase:{self.phase_code};"
            f"session:{self.session_index};focus:{focus}"
        )

    @property
    def visible_title(self) -> str:
        return f"{self.phase_title} · неделя {self.cycle_week}/{self.plan.cycle_length_weeks}"


def sessions_per_week(profile: Profile) -> int:
    if profile.training_structure == TrainingStructure.fullbody:
        return 3
    if profile.split_type == SplitType.push_pull_legs:
        return 3
    if profile.split_type == SplitType.bro_split:
        return 5
    return 4


def default_strategy(profile: Profile) -> dict:
    structure = (profile.training_structure or TrainingStructure.fullbody).value
    split = profile.split_type.value if profile.split_type else None
    goal = (profile.goal or Goal.maintenance).value
    return {
        "version": 1,
        "cycle_length_weeks": DEFAULT_CYCLE_LENGTH_WEEKS,
        "goal": goal,
        "structure": structure,
        "split_type": split,
        "sessions_per_week": sessions_per_week(profile),
        "phases": {str(week): data["code"] for week, data in PHASES.items()},
    }


def plan_matches_profile(plan: WorkoutPlan, profile: Profile) -> bool:
    structure = (profile.training_structure or TrainingStructure.fullbody).value
    split = profile.split_type.value if profile.split_type else None
    strategy = plan.strategy or {}
    return (
        plan.structure == structure
        and plan.split_type == split
        and strategy.get("goal") == (profile.goal or Goal.maintenance).value
    )


async def get_or_create_active_plan(session: AsyncSession, profile: Profile) -> WorkoutPlan:
    result = await session.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == profile.user_id, WorkoutPlan.is_active == True)
        .order_by(WorkoutPlan.created_at.desc())
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    if plan and plan_matches_profile(plan, profile):
        return plan

    if plan:
        plan.is_active = False

    strategy = default_strategy(profile)
    plan = WorkoutPlan(
        user_id=profile.user_id,
        name="Основной тренировочный цикл",
        structure=strategy["structure"],
        split_type=strategy["split_type"],
        cycle_length_weeks=strategy["cycle_length_weeks"],
        current_week=1,
        current_session_index=0,
        strategy=strategy,
        is_active=True,
    )
    session.add(plan)
    await session.flush()
    return plan


async def completed_workout_count(session: AsyncSession, user_id: int, plan_id: int | None = None) -> int:
    query = select(func.count(WorkoutSession.id)).where(
        WorkoutSession.user_id == user_id,
        WorkoutSession.status == SessionStatus.completed,
    )
    if plan_id:
        query = query.where(WorkoutSession.plan_id == plan_id)
    result = await session.execute(query)
    return int(result.scalar() or 0)


async def strategy_context_for_next_session(
    session: AsyncSession,
    profile: Profile,
    target_groups: list[str],
) -> StrategyContext:
    plan = await get_or_create_active_plan(session, profile)
    completed_count = await completed_workout_count(session, profile.user_id, plan.id)
    per_week = int((plan.strategy or {}).get("sessions_per_week") or sessions_per_week(profile))
    per_week = max(1, per_week)
    cycle_length = int(plan.cycle_length_weeks or DEFAULT_CYCLE_LENGTH_WEEKS)
    cycle_week = ((completed_count // per_week) % cycle_length) + 1
    session_index = completed_count % per_week
    phase = PHASES.get(cycle_week, PHASES[DEFAULT_CYCLE_LENGTH_WEEKS])

    plan.current_week = cycle_week
    plan.current_session_index = session_index

    return StrategyContext(
        plan=plan,
        completed_count=completed_count,
        cycle_week=cycle_week,
        session_index=session_index,
        sessions_per_week=per_week,
        phase_code=phase["code"],
        phase_title=phase["title"],
        focus_groups=target_groups,
        volume_factor=float(phase["volume_factor"]),
        intensity_factor=float(phase["intensity_factor"]),
        rest_factor=float(phase["rest_factor"]),
    )


def parse_strategy_note(notes: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for chunk in (notes or "").split(";"):
        if ":" not in chunk:
            continue
        key, value = chunk.split(":", 1)
        if key and value:
            result[key] = value
    return result


def format_strategy_note_title(notes: str | None, cycle_length_weeks: int = DEFAULT_CYCLE_LENGTH_WEEKS) -> str | None:
    parsed = parse_strategy_note(notes)
    week_raw = parsed.get("week")
    phase_code = parsed.get("phase")
    if not week_raw or not phase_code:
        return None
    title = next((phase["title"] for phase in PHASES.values() if phase["code"] == phase_code), phase_code)
    return f"{title} · неделя {week_raw}/{cycle_length_weeks}"
