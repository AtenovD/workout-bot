"""
Stats chart service — generates progress chart images using matplotlib.
"""
import io
from datetime import date, timedelta

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from models.workout import WorkoutSession, ExerciseSet, SessionExercise, SessionStatus
from models.user import User


async def generate_volume_chart(session: AsyncSession, user: User, days: int = 30) -> bytes:
    """Generate a weekly volume chart. Returns PNG bytes."""
    since = date.today() - timedelta(days=days)

    res = await session.execute(
        select(WorkoutSession.id, WorkoutSession.completed_at, WorkoutSession.total_volume_kg)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.completed_at >= since,
        )
        .order_by(WorkoutSession.completed_at)
    )
    rows = res.all()

    if not rows:
        return _empty_chart("Нет данных за последние 30 дней")

    dates = []
    volumes = []
    for row in rows:
        volume = float(row.total_volume_kg or 0)
        if volume <= 0:
            fallback_res = await session.execute(
                select(func.sum(ExerciseSet.reps_done * ExerciseSet.weight_kg))
                .join(SessionExercise, ExerciseSet.session_exercise_id == SessionExercise.id)
                .where(SessionExercise.session_id == row.id)
            )
            volume = float(fallback_res.scalar() or 0)
        dates.append(row.completed_at.date())
        volumes.append(volume)

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.bar(dates, volumes, color="#4f8ef7", width=0.6, edgecolor="none")
    ax.set_title("📊 Объём тренировок (кг)", color="white", fontsize=13, pad=12)
    ax.set_xlabel("Дата", color="#aaa", fontsize=9)
    ax.set_ylabel("Объём, кг", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", color="#aaa", fontsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


async def generate_weight_chart(session: AsyncSession, user: User, days: int = 90) -> bytes:
    """Generate body weight trend chart."""
    from models.body_measurement import BodyMeasurement
    since = date.today() - timedelta(days=days)

    res = await session.execute(
        select(BodyMeasurement.date, BodyMeasurement.weight_kg)
        .where(BodyMeasurement.user_id == user.id, BodyMeasurement.date >= since)
        .order_by(BodyMeasurement.date)
    )
    rows = res.all()

    if not rows:
        return _empty_chart("Нет данных о весе")

    dates = [r.date for r in rows]
    weights = [float(r.weight_kg) for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.plot(dates, weights, color="#4f8ef7", linewidth=2, marker="o", markersize=4)
    ax.fill_between(dates, weights, alpha=0.15, color="#4f8ef7")
    ax.set_title("⚖️ Динамика веса", color="white", fontsize=13, pad=12)
    ax.set_xlabel("Дата", color="#aaa", fontsize=9)
    ax.set_ylabel("Вес, кг", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _empty_chart(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.text(0.5, 0.5, message, transform=ax.transAxes, ha="center", va="center",
            color="#aaa", fontsize=12)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
