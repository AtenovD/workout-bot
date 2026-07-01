import io
from datetime import date, datetime, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.workout import ExerciseSet, SessionExercise, SessionStatus, WorkoutSession


async def generate_volume_chart(session: AsyncSession, user: User, days: int = 30, lang: str = "ru") -> bytes:
    since = date.today() - timedelta(days=days)
    rows = (
        await session.execute(
            select(WorkoutSession.id, WorkoutSession.completed_at, WorkoutSession.total_volume_kg)
            .where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.status == SessionStatus.completed,
                WorkoutSession.completed_at >= since,
            )
            .order_by(WorkoutSession.completed_at)
        )
    ).all()

    if not rows:
        message = "No data for the last 30 days" if lang == "en" else "Нет данных за последние 30 дней"
        return _empty_chart(message)

    dates = []
    volumes = []
    for row in rows:
        volume = float(row.total_volume_kg or 0)
        if volume <= 0:
            volume = float(
                (
                    await session.execute(
                        select(func.sum(ExerciseSet.reps_done * ExerciseSet.weight_kg))
                        .join(SessionExercise, ExerciseSet.session_exercise_id == SessionExercise.id)
                        .where(SessionExercise.session_id == row.id)
                    )
                ).scalar()
                or 0
            )
        dates.append(row.completed_at.date())
        volumes.append(volume)

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.bar(dates, volumes, color="#4f8ef7", width=0.6, edgecolor="none")
    ax.set_title("Training volume (kg)" if lang == "en" else "Объем тренировок (кг)", color="white", fontsize=13, pad=12)
    ax.set_xlabel("Date" if lang == "en" else "Дата", color="#aaa", fontsize=9)
    ax.set_ylabel("Volume, kg" if lang == "en" else "Объем, кг", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", color="#aaa", fontsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    plt.tight_layout()
    return _fig_to_png(fig)


async def generate_weight_chart(session: AsyncSession, user: User, days: int = 90, lang: str = "ru") -> bytes:
    from models.body_measurement import BodyMeasurement

    since = datetime.combine(date.today() - timedelta(days=days), datetime.min.time())
    rows = (
        await session.execute(
            select(BodyMeasurement.recorded_at, BodyMeasurement.weight_kg)
            .where(
                BodyMeasurement.user_id == user.telegram_id,
                BodyMeasurement.recorded_at >= since,
                BodyMeasurement.weight_kg.is_not(None),
            )
            .order_by(BodyMeasurement.recorded_at)
        )
    ).all()

    if not rows:
        message = "No body weight data yet" if lang == "en" else "Нет данных о весе"
        return _empty_chart(message)

    dates = [row.recorded_at.date() if hasattr(row.recorded_at, "date") else row.recorded_at for row in rows]
    weights = [float(row.weight_kg) for row in rows]

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.plot(dates, weights, color="#4f8ef7", linewidth=2, marker="o", markersize=4)
    ax.fill_between(dates, weights, alpha=0.15, color="#4f8ef7")
    ax.set_title("Body weight trend" if lang == "en" else "Динамика веса", color="white", fontsize=13, pad=12)
    ax.set_xlabel("Date" if lang == "en" else "Дата", color="#aaa", fontsize=9)
    ax.set_ylabel("Weight, kg" if lang == "en" else "Вес, кг", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    plt.tight_layout()
    return _fig_to_png(fig)


def _empty_chart(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.text(0.5, 0.5, message, transform=ax.transAxes, ha="center", va="center", color="#aaa", fontsize=12)
    ax.axis("off")
    return _fig_to_png(fig, dpi=100)


def _fig_to_png(fig, dpi: int = 120) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
