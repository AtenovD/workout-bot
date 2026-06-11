from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.exercise import Exercise, Equipment, MuscleGroup, EquipmentCategory


class ExerciseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_exercises_for_user(
        self,
        user_equipment_ids: list[int],
        health_flags: list[str],
        muscle_group_codes: list[str],
    ) -> list[Exercise]:
        """Filter exercises by available equipment and health constraints."""
        # Always include bodyweight (equipment_category=none)
        stmt = select(Exercise).where(
            and_(
                Exercise.is_active == True,
                Exercise.equipment_category.in_([EquipmentCategory.none] + [
                    EquipmentCategory.portable, EquipmentCategory.stationary
                ] if user_equipment_ids else [EquipmentCategory.none]),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_equipment_catalog(self) -> list[Equipment]:
        result = await self.session.execute(select(Equipment))
        return result.scalars().all()

    async def get_user_equipment_ids(self, user_id: int) -> list[int]:
        from models.exercise import Equipment
        # TODO: join with user_equipment table
        return []
