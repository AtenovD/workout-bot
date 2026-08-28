from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.workout import WorkoutSession, SessionExercise, ExerciseSet, SessionStatus
from datetime import date


class WorkoutRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user_id: int, **kwargs) -> WorkoutSession:
        ws = WorkoutSession(user_id=user_id, **kwargs)
        self.session.add(ws)
        await self.session.commit()
        await self.session.refresh(ws)
        return ws

    async def get_active_session(self, user_id: int) -> WorkoutSession | None:
        result = await self.session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .where(WorkoutSession.status == SessionStatus.in_progress)
            .order_by(desc(WorkoutSession.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_recent_sessions(self, user_id: int, limit: int = 10) -> list[WorkoutSession]:
        result = await self.session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .where(WorkoutSession.status == SessionStatus.completed)
            .order_by(desc(WorkoutSession.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def complete_session(self, session_id: int, **kwargs) -> WorkoutSession:
        result = await self.session.execute(select(WorkoutSession).where(WorkoutSession.id == session_id))
        ws = result.scalar_one()
        ws.status = SessionStatus.completed
        for k, v in kwargs.items():
            setattr(ws, k, v)
        await self.session.commit()
        return ws

    async def add_set(self, session_exercise_id: int, set_number: int, reps_done: int, weight_kg: float, rpe: int | None = None) -> ExerciseSet:
        exercise_set = ExerciseSet(
            session_exercise_id=session_exercise_id,
            set_number=set_number,
            reps_done=reps_done,
            weight_kg=weight_kg,
            rpe=rpe,
        )
        self.session.add(exercise_set)
        await self.session.commit()
        return exercise_set
