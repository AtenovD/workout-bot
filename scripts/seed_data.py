"""
Seed script — combines all exercise data and populates all reference tables.
Run: python -m scripts.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from core.db import AsyncSessionLocal, engine, Base
from models.user import User
from models.profile import Profile
from models.exercise import Equipment, MuscleGroup, Exercise, EquipmentCategory, ExerciseType
from models.gamification import Achievement, AchievementCategory, AchievementTier, UserStats
from scripts.exercises_chest_back import EXERCISES_CHEST_BACK
from scripts.exercises_rest import EXERCISES_REST
# ALL_EXTRA_EXERCISES removed — exercises without GIFs
from scripts.exercises_new import EXERCISES_NEW


# ─── Reference: Equipment ─────────────────────────────────────────────────────
EQUIPMENT_DATA = [
    # ── Без инвентаря ──
    {"code": "bodyweight", "name_ru": "Свой вес", "name_en": "Bodyweight", "category": "none", "icon": "🧘",
     "photo_url": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400"},

    # ── Переносной ──
    {"code": "dumbbell", "name_ru": "Гантели", "name_en": "Dumbbells", "category": "portable", "icon": "💪",
     "photo_url": "https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=400"},
    {"code": "kettlebell", "name_ru": "Гиря", "name_en": "Kettlebell", "category": "portable", "icon": "⚖️",
     "photo_url": "https://images.unsplash.com/photo-1604247584233-99c80a8a0e1c?w=400"},
    {"code": "resistance_band", "name_ru": "Эспандер / Резинки", "name_en": "Resistance Bands", "category": "portable", "icon": "🔗",
     "photo_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400"},
    {"code": "jump_rope", "name_ru": "Скакалка", "name_en": "Jump Rope", "category": "portable", "icon": "🪢",
     "photo_url": "https://images.unsplash.com/photo-1434596922112-19c563067271?w=400"},
    {"code": "trx", "name_ru": "TRX петли", "name_en": "TRX Straps", "category": "portable", "icon": "⛓️",
     "photo_url": "https://images.unsplash.com/photo-1517344884509-a0c97ec11bcc?w=400"},
    {"code": "fitball", "name_ru": "Фитбол", "name_en": "Fitness Ball", "category": "portable", "icon": "🟣",
     "photo_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400"},
    {"code": "medicine_ball", "name_ru": "Медбол", "name_en": "Medicine Ball", "category": "portable", "icon": "🔴",
     "photo_url": "https://images.unsplash.com/photo-1607962837359-5e7e89f86776?w=400"},
    {"code": "ab_wheel", "name_ru": "Ролик для пресса", "name_en": "Ab Wheel", "category": "portable", "icon": "🎡",
     "photo_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400"},
    {"code": "barbell_ez_short", "name_ru": "EZ-гриф", "name_en": "EZ Curl Bar", "category": "portable", "icon": "〰️",
     "photo_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=400"},

    # ── Стационарный ──
    {"code": "barbell_standard", "name_ru": "Штанга", "name_en": "Barbell", "category": "stationary", "icon": "🏋️",
     "photo_url": "https://images.unsplash.com/photo-1534368786749-d63b77b1c0fb?w=400"},
    {"code": "smith_machine", "name_ru": "Машина Смита", "name_en": "Smith Machine", "category": "stationary", "icon": "🤖",
     "photo_url": "https://images.unsplash.com/photo-1652363722833-509b3aac287b?w=400"},
    {"code": "bench_flat", "name_ru": "Скамья горизонтальная", "name_en": "Flat Bench", "category": "stationary", "icon": "🪑",
     "photo_url": "https://images.unsplash.com/photo-1517963879433-6ad2b056d712?w=400"},
    {"code": "bench_incline", "name_ru": "Скамья с наклоном", "name_en": "Incline Bench", "category": "stationary", "icon": "📐",
     "photo_url": "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=400"},
    {"code": "pullup_bar", "name_ru": "Турник", "name_en": "Pull-up Bar", "category": "stationary", "icon": "🔝",
     "photo_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400"},
    {"code": "dip_bar", "name_ru": "Брусья", "name_en": "Dip Bars", "category": "stationary", "icon": "📏",
     "photo_url": "https://images.unsplash.com/photo-1652363722833-509b3aac287b?w=400"},
    {"code": "cable_machine", "name_ru": "Блочный тренажёр (кроссовер)", "name_en": "Cable Crossover", "category": "stationary", "icon": "🪢",
     "photo_url": "https://images.unsplash.com/photo-1576678927484-cc907957088c?w=400"},
    {"code": "lat_pulldown", "name_ru": "Тяга верхнего блока", "name_en": "Lat Pulldown", "category": "stationary", "icon": "⬇️",
     "photo_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=400"},
    {"code": "seated_row", "name_ru": "Тяга нижнего блока / к поясу сидя", "name_en": "Seated Row", "category": "stationary", "icon": "🚣",
     "photo_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400"},
    {"code": "leg_press", "name_ru": "Жим ногами", "name_en": "Leg Press", "category": "stationary", "icon": "🦿",
     "photo_url": "https://images.unsplash.com/photo-1652363723082-de3f7e0e5e69?w=400"},
    {"code": "hack_squat", "name_ru": "Гакк-приседания", "name_en": "Hack Squat", "category": "stationary", "icon": "⛰️",
     "photo_url": "https://images.unsplash.com/photo-1652363723038-cb4d2c8e51fe?w=400"},
    {"code": "leg_extension", "name_ru": "Разгибание ног", "name_en": "Leg Extension", "category": "stationary", "icon": "🦵",
     "photo_url": "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=400"},
    {"code": "leg_curl", "name_ru": "Сгибание ног", "name_en": "Leg Curl", "category": "stationary", "icon": "🦿",
     "photo_url": "https://images.unsplash.com/photo-1652363723038-cb4d2c8e51fe?w=400"},
    {"code": "chest_fly", "name_ru": "Пек-дек (тренажёр бабочка)", "name_en": "Pec Deck", "category": "stationary", "icon": "🦋",
     "photo_url": "https://images.unsplash.com/photo-1652363722900-9b0e8e3c9e3a?w=400"},
    {"code": "shoulder_press_machine", "name_ru": "Жим плечами в тренажёре", "name_en": "Shoulder Press Machine", "category": "stationary", "icon": "🏋️",
     "photo_url": "https://images.unsplash.com/photo-1652363722833-509b3aac287b?w=400"},
    {"code": "calf_machine", "name_ru": "Тренажёр на икры", "name_en": "Calf Machine", "category": "stationary", "icon": "🦶",
     "photo_url": "https://images.unsplash.com/photo-1652363723038-cb4d2c8e51fe?w=400"},
    {"code": "hyperextension", "name_ru": "Гиперэкстензия", "name_en": "Hyperextension", "category": "stationary", "icon": "↩️",
     "photo_url": "https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=400"},
    {"code": "gymnastics_rings", "name_ru": "Кольца гимнастические", "name_en": "Gymnastics Rings", "category": "stationary", "icon": "⭕",
     "photo_url": "https://images.unsplash.com/photo-1598971639058-fab3c3109a00?w=400"},
    {"code": "treadmill", "name_ru": "Беговая дорожка", "name_en": "Treadmill", "category": "stationary", "icon": "🏃",
     "photo_url": "https://images.unsplash.com/photo-1576678927484-cc907957088c?w=400"},
    {"code": "stationary_bike", "name_ru": "Велотренажёр", "name_en": "Exercise Bike", "category": "stationary", "icon": "🚴",
     "photo_url": "https://images.unsplash.com/photo-1591291621164-2c6367723315?w=400"},
    {"code": "rowing_machine", "name_ru": "Гребной тренажёр", "name_en": "Rowing Machine", "category": "stationary", "icon": "🚣",
     "photo_url": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=400"},
    {"code": "elliptical", "name_ru": "Эллиптический тренажёр", "name_en": "Elliptical", "category": "stationary", "icon": "🌀",
     "photo_url": "https://images.unsplash.com/photo-1591291621060-89264f4d2d6e?w=400"},
]

# ─── Equipment Aliases ──────────────────────────────────────────────────────
# Exercises use mixed naming — some reference English names, others use codes.
EQUIPMENT_ALIASES = {
    "Barbell": "barbell_standard",
    "Dumbbell": "dumbbell",
    "Body Only": "bodyweight",
    "Bands": "resistance_band",
    "Kettlebells": "kettlebell",
    "Cable": "cable_machine",
    "Machine": "cable_machine",
    "Other": "bodyweight",
    "barbell": "barbell_standard",
    "dumbbell": "dumbbell",
    "kettlebell": "kettlebell",
    "cable": "cable_machine",
    "machine": "cable_machine",
}

MUSCLE_GROUP_DATA = [
    {"code": "chest",         "name_ru": "Грудь",                   "name_en": "Chest",         "body_part": "upper_body"},
    {"code": "upper_chest",   "name_ru": "Верхняя грудь",           "name_en": "Upper Chest",   "body_part": "upper_body"},
    {"code": "lower_chest",   "name_ru": "Нижняя грудь",            "name_en": "Lower Chest",   "body_part": "upper_body"},
    {"code": "lats",          "name_ru": "Широчайшие",              "name_en": "Lats",          "body_part": "upper_body"},
    {"code": "middle_back",   "name_ru": "Средняя часть спины",     "name_en": "Middle Back",   "body_part": "upper_body"},
    {"code": "lower_back",    "name_ru": "Поясница",                "name_en": "Lower Back",    "body_part": "upper_body"},
    {"code": "traps",         "name_ru": "Трапеции",                "name_en": "Trapezius",     "body_part": "upper_body"},
    {"code": "front_delts",   "name_ru": "Передние дельты",         "name_en": "Front Delts",   "body_part": "upper_body"},
    {"code": "side_delts",    "name_ru": "Боковые дельты",          "name_en": "Side Delts",    "body_part": "upper_body"},
    {"code": "rear_delts",    "name_ru": "Задние дельты",           "name_en": "Rear Delts",    "body_part": "upper_body"},
    {"code": "biceps",        "name_ru": "Бицепс",                  "name_en": "Biceps",        "body_part": "upper_body"},
    {"code": "triceps",       "name_ru": "Трицепс",                 "name_en": "Triceps",       "body_part": "upper_body"},
    {"code": "forearms",      "name_ru": "Предплечья",              "name_en": "Forearms",      "body_part": "upper_body"},
    {"code": "quadriceps",    "name_ru": "Квадрицепс",              "name_en": "Quadriceps",    "body_part": "lower_body"},
    {"code": "hamstrings",    "name_ru": "Бицепс бедра",            "name_en": "Hamstrings",    "body_part": "lower_body"},
    {"code": "glutes",        "name_ru": "Ягодицы",                 "name_en": "Glutes",        "body_part": "lower_body"},
    {"code": "calves",        "name_ru": "Икры",                    "name_en": "Calves",        "body_part": "lower_body"},
    {"code": "abs",           "name_ru": "Пресс",                   "name_en": "Abs",           "body_part": "core"},
    {"code": "obliques",      "name_ru": "Косые мышцы живота",      "name_en": "Obliques",      "body_part": "core"},
    {"code": "full_body",     "name_ru": "Всё тело",                "name_en": "Full Body",     "body_part": "full_body"},
]

# ─── Achievements ─────────────────────────────────────────────────────────────
ACHIEVEMENTS_DATA = [
    # Consistency
    {"code": "first_workout",    "name": "Первый шаг",         "icon": "👟", "description": "Выполни первую тренировку",      "category": "consistency", "tier": "bronze",   "xp_reward": 50,  "condition": {"type": "total_workouts", "value": 1}},
    {"code": "workouts_5",       "name": "Разминка",           "icon": "🔥", "description": "5 тренировок выполнено",         "category": "consistency", "tier": "bronze",   "xp_reward": 100, "condition": {"type": "total_workouts", "value": 5}},
    {"code": "workouts_10",      "name": "Втянулся",           "icon": "💪", "description": "10 тренировок выполнено",        "category": "consistency", "tier": "bronze",   "xp_reward": 150, "condition": {"type": "total_workouts", "value": 10}},
    {"code": "workouts_25",      "name": "Постоянство",        "icon": "📅", "description": "25 тренировок",                 "category": "consistency", "tier": "silver",   "xp_reward": 250, "condition": {"type": "total_workouts", "value": 25}},
    {"code": "workouts_50",      "name": "Полсотни",           "icon": "🥈", "description": "50 тренировок",                 "category": "consistency", "tier": "silver",   "xp_reward": 400, "condition": {"type": "total_workouts", "value": 50}},
    {"code": "workouts_100",     "name": "Сотник",             "icon": "💯", "description": "100 тренировок",                "category": "consistency", "tier": "gold",     "xp_reward": 750, "condition": {"type": "total_workouts", "value": 100}},
    {"code": "workouts_250",     "name": "Легенда зала",       "icon": "🏆", "description": "250 тренировок",                "category": "consistency", "tier": "platinum", "xp_reward": 2000,"condition": {"type": "total_workouts", "value": 250}},
    # Streaks
    {"code": "streak_3",         "name": "Три дня подряд",     "icon": "🔥", "description": "Стрик 3 дня",                   "category": "consistency", "tier": "bronze",   "xp_reward": 75,  "condition": {"type": "streak", "value": 3}},
    {"code": "streak_7",         "name": "Неделя без пропусков","icon": "📆","description": "Стрик 7 дней",                  "category": "consistency", "tier": "silver",   "xp_reward": 200, "condition": {"type": "streak", "value": 7}},
    {"code": "streak_14",        "name": "Две недели",         "icon": "⚡", "description": "Стрик 14 дней",                 "category": "consistency", "tier": "silver",   "xp_reward": 350, "condition": {"type": "streak", "value": 14}},
    {"code": "streak_30",        "name": "Железная воля",      "icon": "🔱", "description": "Стрик 30 дней",                 "category": "consistency", "tier": "gold",     "xp_reward": 700, "condition": {"type": "streak", "value": 30}},
    {"code": "streak_100",       "name": "Машина",             "icon": "🤖", "description": "Стрик 100 дней",                "category": "consistency", "tier": "platinum", "xp_reward": 3000,"condition": {"type": "streak", "value": 100}},
    # Volume
    {"code": "volume_1t",        "name": "Тонна железа",       "icon": "⚖️", "description": "Поднял суммарно 1 000 кг",     "category": "volume",      "tier": "bronze",   "xp_reward": 100, "condition": {"type": "total_volume", "value": 1000}},
    {"code": "volume_10t",       "name": "10 тонн",            "icon": "🏗",  "description": "Поднял суммарно 10 000 кг",    "category": "volume",      "tier": "silver",   "xp_reward": 300, "condition": {"type": "total_volume", "value": 10000}},
    {"code": "volume_50t",       "name": "50 тонн",            "icon": "🦍", "description": "Поднял суммарно 50 000 кг",    "category": "volume",      "tier": "gold",     "xp_reward": 800, "condition": {"type": "total_volume", "value": 50000}},
    {"code": "volume_session_5k","name": "5К за раз",          "icon": "💥", "description": "5 000 кг за одну тренировку",  "category": "volume",      "tier": "gold",     "xp_reward": 500, "condition": {"type": "session_volume", "value": 5000}},
    # Levels
    {"code": "level_5",          "name": "Опытный",            "icon": "⭐", "description": "Достигни 5-го уровня",          "category": "milestone",   "tier": "bronze",   "xp_reward": 100, "condition": {"type": "level", "value": 5}},
    {"code": "level_10",         "name": "Профессионал",       "icon": "🌟", "description": "Достигни 10-го уровня",         "category": "milestone",   "tier": "silver",   "xp_reward": 300, "condition": {"type": "level", "value": 10}},
    {"code": "level_20",         "name": "Мастер",             "icon": "💎", "description": "Достигни 20-го уровня",         "category": "milestone",   "tier": "gold",     "xp_reward": 1000,"condition": {"type": "level", "value": 20}},
    {"code": "level_50",         "name": "Элита",              "icon": "👑", "description": "Достигни 50-го уровня",         "category": "milestone",   "tier": "platinum", "xp_reward": 5000,"condition": {"type": "level", "value": 50}},
    # PRs
    {"code": "pr_1",             "name": "Первый рекорд",      "icon": "🏅", "description": "Установи первый личный рекорд", "category": "strength",    "tier": "bronze",   "xp_reward": 100, "condition": {"type": "pr_count", "value": 1}},
    {"code": "pr_10",            "name": "10 рекордов",        "icon": "🎯", "description": "10 личных рекордов",            "category": "strength",    "tier": "silver",   "xp_reward": 300, "condition": {"type": "pr_count", "value": 10}},
    {"code": "pr_25",            "name": "Рекордсмен",         "icon": "🏆", "description": "25 личных рекордов",            "category": "strength",    "tier": "gold",     "xp_reward": 750, "condition": {"type": "pr_count", "value": 25}},
    # Special
    {"code": "early_bird",       "name": "Ранняя пташка",      "icon": "🌅", "description": "Тренировка до 7 утра",          "category": "special",     "tier": "silver",   "xp_reward": 200, "condition": {"type": "workout_before_hour", "value": 7}},
    {"code": "night_owl",        "name": "Сова",               "icon": "🦉", "description": "Тренировка после 22:00",        "category": "special",     "tier": "bronze",   "xp_reward": 150, "condition": {"type": "workout_after_hour", "value": 22}},
    {"code": "comeback",         "name": "Возвращение",        "icon": "🦅", "description": "Вернулся после 30+ дней паузы", "category": "special",     "tier": "gold",     "xp_reward": 500, "condition": {"type": "return_after_days", "value": 30}},
]


async def insert_or_update(session, model_class, unique_field, items):
    count_new = 0
    for item_data in items:
        res = await session.execute(
            select(model_class).where(getattr(model_class, unique_field) == item_data[unique_field])
        )
        existing = res.scalar_one_or_none()
        if not existing:
            session.add(model_class(**item_data))
            count_new += 1
        else:
            for k, v in item_data.items():
                setattr(existing, k, v)
    await session.commit()
    return count_new


async def seed_exercises(session, equipment_map, muscle_map):
    """Seed all exercises from all source files."""
    all_exercises = EXERCISES_CHEST_BACK + EXERCISES_REST + EXERCISES_NEW
    count_new = 0
    for ex in all_exercises:
        res = await session.execute(select(Exercise).where(Exercise.code == ex["code"]))
        existing = res.scalar_one_or_none()

        muscle_code = ex.get("muscle")
        muscle_id = muscle_map.get(muscle_code)
        eq_code = ex.get("equipment")
        # Use alias map to resolve equipment code
        resolved_code = EQUIPMENT_ALIASES.get(eq_code, eq_code) if eq_code else None
        eq_id = equipment_map.get(resolved_code) if resolved_code else None

        # Use eq_cat from exercise data, fallback to equipment record
        eq_cat_str = ex.get("eq_cat")
        if eq_cat_str:
            eq_cat = EquipmentCategory(eq_cat_str)
        elif eq_id:
            eq_resolved = await session.get(Equipment, eq_id)
            eq_cat = eq_resolved.category if eq_resolved else EquipmentCategory.none
        else:
            eq_cat = EquipmentCategory.none

        ex_type_map = {"compound": ExerciseType.compound, "isolation": ExerciseType.isolation,
                       "cardio": ExerciseType.cardio, "mobility": ExerciseType.mobility}
        ex_type = ex_type_map.get(ex.get("type", "compound"), ExerciseType.compound)

        fields = {
            "code": ex["code"],
            "name_ru": ex["name_ru"],
            "name_en": ex["name_en"],
            "description": ex.get("description"),
            "instructions": ex.get("instructions"),
            "tips": ex.get("tips"),
            "common_mistakes": ex.get("common_mistakes"),
            "primary_muscle_group_id": muscle_id,
            "required_equipment_id": eq_id,
            "equipment_category": eq_cat,
            "exercise_type": ex_type,
            "difficulty": ex.get("difficulty", 3),
            "met_value": ex.get("met_value"),
            "gif_url": ex.get("gif_url"),
            "photo_url": ex.get("photo_url"),
            "is_active": True,
        }

        if not existing:
            session.add(Exercise(**fields))
            count_new += 1
        else:
            for k, v in fields.items():
                setattr(existing, k, v)

    await session.commit()
    return count_new


async def main():
    # Tables are already created by migrations
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Cleanup: remove legacy equipment records with bad names
        from sqlalchemy import delete
        KNOWN_CODES = [e["code"] for e in EQUIPMENT_DATA]
        await session.execute(
            delete(Equipment).where(Equipment.code.not_in(KNOWN_CODES))
        )
        # Fix any stale name_ru that slipped through (e.g. "Тренажёр", "Блочный тренажёр")
        BAD_NAMES = ["Тренажёр", "Блочный тренажёр", "Тренажор"]
        for bad in BAD_NAMES:
            res = await session.execute(select(Equipment).where(Equipment.name_ru == bad))
            old_eq = res.scalars().all()
            for eq in old_eq:
                await session.delete(eq)
        await session.commit()

        print("Seeding equipment...")
        eq_data = [{k: v for k, v in e.items() if k != "icon"} for e in EQUIPMENT_DATA]
        for item in EQUIPMENT_DATA:
            d = {"code": item["code"], "name_ru": item["name_ru"], "name_en": item["name_en"],
                 "category": EquipmentCategory(item["category"]), "icon": item.get("icon"),
                 "photo_url": item.get("photo_url", "")}
            res = await session.execute(select(Equipment).where(Equipment.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(Equipment(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        await session.commit()

        print("Seeding muscle groups...")
        for item in MUSCLE_GROUP_DATA:
            res = await session.execute(select(MuscleGroup).where(MuscleGroup.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(MuscleGroup(**item))
            else:
                for k, v in item.items():
                    setattr(existing, k, v)
        await session.commit()

        # Build lookup maps
        eq_res = await session.execute(select(Equipment))
        equipment_map = {e.code: e.id for e in eq_res.scalars()}
        mg_res = await session.execute(select(MuscleGroup))
        muscle_map = {m.code: m.id for m in mg_res.scalars()}

        print("Seeding exercises...")
        new_ex = await seed_exercises(session, equipment_map, muscle_map)
        total = len(EXERCISES_CHEST_BACK) + len(EXERCISES_REST) + len(EXERCISES_NEW)
        print(f"  Exercises: {total} total, {new_ex} new")

        print("Seeding achievements...")
        for item in ACHIEVEMENTS_DATA:
            d = {
                "code": item["code"], "name": item["name"], "icon": item["icon"],
                "description": item["description"],
                "category": AchievementCategory(item["category"]),
                "tier": AchievementTier(item["tier"]),
                "xp_reward": item["xp_reward"],
                "condition": item["condition"],
            }
            res = await session.execute(select(Achievement).where(Achievement.code == item["code"]))
            existing = res.scalar_one_or_none()
            if not existing:
                session.add(Achievement(**d))
            else:
                for k, v in d.items():
                    setattr(existing, k, v)
        await session.commit()
        print(f"  Achievements: {len(ACHIEVEMENTS_DATA)}")

        print("\n✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
