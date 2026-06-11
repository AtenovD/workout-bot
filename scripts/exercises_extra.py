"""
Extended exercise database — 80+ exercises across all muscle groups with GIF URLs.
GIF source: ExerciseDB (https://github.com/yuhonas/free-exercise-db, MIT License)
Base URL: https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/
"""

# GIF base URL from free-exercise-db
_GIF = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

EXERCISES_LEGS = [
    # ─── Квадрицепс / Ягодицы ────────────────────────────────────────
    {"code": "squat_barbell", "name_ru": "Приседания со штангой", "name_en": "Barbell Squat",
     "muscle": "quads", "equipment": "barbell", "type": "compound", "difficulty": 4,
     "met_value": 7.0, "gif_url": _GIF + "0150/0150.gif",
     "description": "Базовое упражнение на квадрицепс и ягодицы",
     "instructions": ["Встань под штангу на стойке", "Возьмись широким хватом", "Присядь до параллели бёдер с полом", "Встань, не округляя спину"],
     "tips": ["Колени не заваливай вовнутрь", "Смотри прямо перед собой"]},

    {"code": "squat_goblet", "name_ru": "Приседания с гирей (Гоблет)", "name_en": "Goblet Squat",
     "muscle": "quads", "equipment": "kettlebell", "type": "compound", "difficulty": 2,
     "met_value": 6.0, "gif_url": _GIF + "0716/0716.gif",
     "instructions": ["Держи гирю у груди", "Ноги шире плеч", "Присядь глубоко", "Встань"],
     "tips": ["Держи гирю близко к телу", "Глубокий сед улучшает мобильность"]},

    {"code": "squat_front", "name_ru": "Фронтальные приседания", "name_en": "Front Squat",
     "muscle": "quads", "equipment": "barbell", "type": "compound", "difficulty": 5,
     "met_value": 7.5, "gif_url": _GIF + "0539/0539.gif",
     "instructions": ["Штанга лежит на передних дельтах", "Локти подняты вверх", "Присядь вертикально"],
     "tips": ["Требует хорошей мобильности запястий"]},

    {"code": "leg_press", "name_ru": "Жим ногами", "name_en": "Leg Press",
     "muscle": "quads", "equipment": "machine", "type": "compound", "difficulty": 2,
     "met_value": 5.0, "gif_url": _GIF + "0351/0351.gif",
     "instructions": ["Сядь в тренажёр", "Поставь ноги на платформу шире плеч", "Жми платформу вверх", "Согни до 90°"],
     "tips": ["Не блокируй колени в верхней точке"]},

    {"code": "leg_extension", "name_ru": "Разгибания ног", "name_en": "Leg Extension",
     "muscle": "quads", "equipment": "machine", "type": "isolation", "difficulty": 1,
     "met_value": 4.0, "gif_url": _GIF + "0344/0344.gif",
     "instructions": ["Сядь в тренажёр", "Подложи подушку под голени", "Разогни ноги до конца"],
     "tips": ["Задержись на 1 сек в верхней точке"]},

    {"code": "lunge_barbell", "name_ru": "Выпады со штангой", "name_en": "Barbell Lunge",
     "muscle": "quads", "equipment": "barbell", "type": "compound", "difficulty": 3,
     "met_value": 6.0, "gif_url": _GIF + "0030/0030.gif",
     "instructions": ["Штанга на плечах", "Шаг вперёд", "Опусти заднее колено до пола", "Встань и смени ногу"],
     "tips": ["Держи корпус прямо"]},

    {"code": "lunge_dumbbell", "name_ru": "Выпады с гантелями", "name_en": "Dumbbell Lunge",
     "muscle": "quads", "equipment": "dumbbell", "type": "compound", "difficulty": 2,
     "met_value": 5.5, "gif_url": _GIF + "0629/0629.gif",
     "instructions": ["Гантели в руках", "Шаги вперёд попеременно"],
     "tips": ["Не допускай заваливания корпуса"]},

    {"code": "bulgarian_split_squat", "name_ru": "Болгарские сплит-приседания", "name_en": "Bulgarian Split Squat",
     "muscle": "quads", "equipment": "dumbbell", "type": "compound", "difficulty": 4,
     "met_value": 6.5, "gif_url": _GIF + "1169/1169.gif",
     "instructions": ["Задняя нога на скамье", "Присядь на передней ноге", "Бедро параллельно полу"],
     "tips": ["Одно из лучших упражнений для ног без штанги"]},

    # ─── Задняя поверхность бедра / Ягодицы ─────────────────────────
    {"code": "rdl_barbell", "name_ru": "Румынская тяга (штанга)", "name_en": "Romanian Deadlift",
     "muscle": "hamstrings", "equipment": "barbell", "type": "compound", "difficulty": 3,
     "met_value": 6.0, "gif_url": _GIF + "0490/0490.gif",
     "instructions": ["Штанга в руках хватом сверху", "Наклоняйся, сохраняя прогиб в пояснице", "Почувствуй растяжение бицепса бедра"],
     "tips": ["Не скругляй спину", "Штанга ведёт вдоль ног"]},

    {"code": "leg_curl_machine", "name_ru": "Сгибания ног лёжа", "name_en": "Lying Leg Curl",
     "muscle": "hamstrings", "equipment": "machine", "type": "isolation", "difficulty": 1,
     "met_value": 4.0, "gif_url": _GIF + "0358/0358.gif",
     "instructions": ["Ляг лицом вниз", "Согни ноги до максимума"],
     "tips": ["Задержись на 1 сек в верхней точке"]},

    {"code": "hip_thrust", "name_ru": "Ягодичный мост (штанга)", "name_en": "Barbell Hip Thrust",
     "muscle": "glutes", "equipment": "barbell", "type": "compound", "difficulty": 3,
     "met_value": 5.5, "gif_url": _GIF + "0031/0031.gif",
     "instructions": ["Спиной на скамью", "Штанга на бёдрах", "Поднимай таз вверх до прямой линии"],
     "tips": ["Максимально сжимай ягодицы в верхней точке"]},

    {"code": "glute_kickback", "name_ru": "Отведение ноги назад", "name_en": "Cable Glute Kickback",
     "muscle": "glutes", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0062/0062.gif",
     "instructions": ["Прикрепи манжету к кабелю", "Отведи ногу назад, напрягая ягодицу"],
     "tips": ["Не разворачивай таз"]},

    # ─── Икры ──────────────────────────────────────────────────────
    {"code": "calf_raise_standing", "name_ru": "Подъём на носки стоя", "name_en": "Standing Calf Raise",
     "muscle": "calves", "equipment": "machine", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0115/0115.gif",
     "instructions": ["Встань на платформу", "Поднимись на носки максимально высоко", "Медленно опустись"],
     "tips": ["Растягивай икры в нижней точке"]},

    {"code": "calf_raise_seated", "name_ru": "Подъём на носки сидя", "name_en": "Seated Calf Raise",
     "muscle": "calves", "equipment": "machine", "type": "isolation", "difficulty": 1,
     "met_value": 3.0, "gif_url": _GIF + "0117/0117.gif",
     "instructions": ["Сядь в тренажёр", "Положи подушку на колени", "Поднимись на носки"],
     "tips": ["Медленное движение = больше нагрузки"]},
]

EXERCISES_BACK_ADVANCED = [
    # ─── Широчайшие ─────────────────────────────────────────────────
    {"code": "pullup", "name_ru": "Подтягивания", "name_en": "Pull-up",
     "muscle": "lats", "equipment": "pullup_bar", "type": "compound", "difficulty": 4,
     "met_value": 8.0, "gif_url": _GIF + "0472/0472.gif",
     "instructions": ["Хват шире плеч", "Подтянись до подбородка выше перекладины", "Медленно опустись"],
     "tips": ["Не раскачивайся", "Лопатки в начале движения"]},

    {"code": "pullup_close_grip", "name_ru": "Подтягивания узким хватом", "name_en": "Close-Grip Pull-up",
     "muscle": "lats", "equipment": "pullup_bar", "type": "compound", "difficulty": 4,
     "met_value": 7.5, "gif_url": _GIF + "0473/0473.gif",
     "instructions": ["Хват на ширине плеч", "Подтянись, ведя локти к бокам"],
     "tips": ["Больше нагружает нижние широчайшие"]},

    {"code": "lat_pulldown_wide", "name_ru": "Тяга блока широким хватом", "name_en": "Lat Pulldown Wide",
     "muscle": "lats", "equipment": "cable", "type": "compound", "difficulty": 2,
     "met_value": 5.0, "gif_url": _GIF + "0311/0311.gif",
     "instructions": ["Возьмись широким хватом", "Тяни к верхней части груди", "Лопатки сводить внизу"],
     "tips": ["Не отклоняйся назад сильно"]},

    {"code": "lat_pulldown_close", "name_ru": "Тяга блока узким хватом", "name_en": "Lat Pulldown Close",
     "muscle": "lats", "equipment": "cable", "type": "compound", "difficulty": 2,
     "met_value": 5.0, "gif_url": _GIF + "0313/0313.gif",
     "instructions": ["Нейтральный хват (рукоятка V)", "Тяни к нижней части груди"],
     "tips": ["Большой диапазон движения"]},

    {"code": "row_cable_seated", "name_ru": "Горизонтальная тяга блока", "name_en": "Seated Cable Row",
     "muscle": "middle_back", "equipment": "cable", "type": "compound", "difficulty": 2,
     "met_value": 5.0, "gif_url": _GIF + "0526/0526.gif",
     "instructions": ["Сядь, ноги на платформе", "Тяни рукоять к животу", "Сводь лопатки"],
     "tips": ["Не горбись при возврате"]},

    {"code": "row_dumbbell_single", "name_ru": "Тяга гантели в наклоне", "name_en": "One-Arm Dumbbell Row",
     "muscle": "lats", "equipment": "dumbbell", "type": "compound", "difficulty": 2,
     "met_value": 5.5, "gif_url": _GIF + "0201/0201.gif",
     "instructions": ["Коленом и рукой упрись в скамью", "Тяни гантель к поясу", "Локоть ведёт движение"],
     "tips": ["Не поворачивай корпус"]},

    {"code": "tbar_row", "name_ru": "Тяга Т-грифа", "name_en": "T-Bar Row",
     "muscle": "middle_back", "equipment": "barbell", "type": "compound", "difficulty": 3,
     "met_value": 6.0, "gif_url": _GIF + "0600/0600.gif",
     "instructions": ["Наклонись под 45°", "Тяни Т-гриф к груди", "Сводь лопатки"],
     "tips": ["Отличная альтернатива тяге в наклоне"]},

    {"code": "hyperextension", "name_ru": "Гиперэкстензия", "name_en": "Back Extension",
     "muscle": "lower_back", "equipment": "machine", "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0286/0286.gif",
     "instructions": ["Ляг в тренажёр лицом вниз", "Опусти корпус вниз", "Поднимись до прямой линии"],
     "tips": ["Не перегибайся в пояснице"]},
]

EXERCISES_CHEST_ADVANCED = [
    {"code": "bench_press_incline_barbell", "name_ru": "Жим под углом вверх (штанга)", "name_en": "Incline Barbell Press",
     "muscle": "upper_chest", "equipment": "barbell", "type": "compound", "difficulty": 4,
     "met_value": 6.5, "gif_url": _GIF + "0056/0056.gif",
     "instructions": ["Угол скамьи 30-45°", "Хват чуть шире плеч", "Жим вверх"],
     "tips": ["Хорошо нагружает верхнюю часть груди"]},

    {"code": "bench_press_decline", "name_ru": "Жим под углом вниз", "name_en": "Decline Bench Press",
     "muscle": "chest", "equipment": "barbell", "type": "compound", "difficulty": 4,
     "met_value": 6.0, "gif_url": _GIF + "0054/0054.gif",
     "instructions": ["Угол скамьи -15°", "Жим к нижней части груди"],
     "tips": ["Нагружает нижнюю грудь"]},

    {"code": "fly_dumbbell", "name_ru": "Разводка гантелей лёжа", "name_en": "Dumbbell Fly",
     "muscle": "chest", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 4.5, "gif_url": _GIF + "0192/0192.gif",
     "instructions": ["Лёжа на скамье", "Разведи гантели в стороны с лёгким сгибом локтей", "Сведи обратно"],
     "tips": ["Следи за растяжкой грудных"]},

    {"code": "fly_cable_low", "name_ru": "Кроссовер снизу вверх", "name_en": "Cable Fly Low to High",
     "muscle": "upper_chest", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 4.5, "gif_url": _GIF + "0437/0437.gif",
     "instructions": ["Блоки внизу", "Своди руки перед грудью снизу вверх"],
     "tips": ["Отличная нагрузка на верхнюю грудь"]},

    {"code": "fly_cable_high", "name_ru": "Кроссовер сверху вниз", "name_en": "Cable Fly High to Low",
     "muscle": "lower_chest", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 4.5, "gif_url": _GIF + "0436/0436.gif",
     "instructions": ["Блоки сверху", "Своди руки перед грудью сверху вниз"],
     "tips": ["Нижняя часть груди"]},

    {"code": "chest_dip", "name_ru": "Отжимания на брусьях (грудные)", "name_en": "Chest Dip",
     "muscle": "chest", "equipment": "dip_bar", "type": "compound", "difficulty": 3,
     "met_value": 7.0, "gif_url": _GIF + "1010/1010.gif",
     "instructions": ["Наклонись вперёд", "Опустись до локтей 90°", "Оттолкнись вверх"],
     "tips": ["Наклон корпуса вперёд = больше грудных"]},
]

EXERCISES_SHOULDERS = [
    {"code": "ohp_barbell", "name_ru": "Жим штанги стоя", "name_en": "Barbell OHP",
     "muscle": "front_delts", "equipment": "barbell", "type": "compound", "difficulty": 4,
     "met_value": 6.5, "gif_url": _GIF + "0046/0046.gif",
     "instructions": ["Хват чуть шире плеч", "Жми вертикально вверх", "Голова уходит назад при проходе штанги"],
     "tips": ["Не прогибай поясницу"]},

    {"code": "ohp_dumbbell_seated", "name_ru": "Жим гантелей сидя", "name_en": "Seated Dumbbell Press",
     "muscle": "front_delts", "equipment": "dumbbell", "type": "compound", "difficulty": 2,
     "met_value": 5.5, "gif_url": _GIF + "0214/0214.gif",
     "instructions": ["Сядь с прямой спиной", "Гантели у плеч", "Жми вверх до полного разгибания"],
     "tips": ["Стабилизирующие мышцы работают активнее, чем при машине"]},

    {"code": "lateral_raise", "name_ru": "Махи гантелями в стороны", "name_en": "Lateral Raise",
     "muscle": "side_delts", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0328/0328.gif",
     "instructions": ["Небольшой наклон вперёд", "Подними гантели до уровня плеч"],
     "tips": ["Мизинец немного выше большого пальца"]},

    {"code": "lateral_raise_cable", "name_ru": "Махи в стороны у кабеля", "name_en": "Cable Lateral Raise",
     "muscle": "side_delts", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0166/0166.gif",
     "instructions": ["Возьми нижний блок", "Подними руку в сторону через тело"],
     "tips": ["Постоянное натяжение vs гантели"]},

    {"code": "front_raise", "name_ru": "Махи вперёд", "name_en": "Front Raise",
     "muscle": "front_delts", "equipment": "dumbbell", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0235/0235.gif",
     "instructions": ["Поднимай гантели перед собой до уровня плеч"],
     "tips": ["Передние дельты обычно достаточно нагружаются в жимах"]},

    {"code": "reverse_fly", "name_ru": "Разводка на заднюю дельту", "name_en": "Reverse Fly",
     "muscle": "rear_delts", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0498/0498.gif",
     "instructions": ["Наклонись 90°", "Разведи гантели назад-в стороны"],
     "tips": ["Важно для баланса плечевого сустава"]},

    {"code": "face_pull", "name_ru": "Тяга каната к лицу", "name_en": "Face Pull",
     "muscle": "rear_delts", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0224/0224.gif",
     "instructions": ["Канат на уровне головы", "Тяни к лицу, локти высоко", "Разворачивай плечи"],
     "tips": ["Здоровье ротаторной манжеты"]},

    {"code": "arnold_press", "name_ru": "Жим Арнольда", "name_en": "Arnold Press",
     "muscle": "front_delts", "equipment": "dumbbell", "type": "compound", "difficulty": 3,
     "met_value": 5.5, "gif_url": _GIF + "0046/0046.gif",
     "instructions": ["Начни с гантелями перед лицом (ладони к тебе)", "Поворачивай ладони наружу в процессе жима"],
     "tips": ["Большой диапазон движения"]},

    {"code": "shrug_barbell", "name_ru": "Шраги со штангой", "name_en": "Barbell Shrug",
     "muscle": "traps", "equipment": "barbell", "type": "isolation", "difficulty": 1,
     "met_value": 4.0, "gif_url": _GIF + "0562/0562.gif",
     "instructions": ["Штанга в руках", "Поднимай плечи максимально вверх", "Задержись 1 сек"],
     "tips": ["Не вращай плечами"]},
]

EXERCISES_ARMS = [
    # ─── Бицепс ──────────────────────────────────────────────────
    {"code": "curl_barbell", "name_ru": "Подъём штанги на бицепс", "name_en": "Barbell Curl",
     "muscle": "biceps", "equipment": "barbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0031/0031.gif",
     "instructions": ["Хват снизу на ширине плеч", "Сгибай руки к плечам", "Медленно опускай"],
     "tips": ["Локти прижаты к туловищу"]},

    {"code": "curl_dumbbell_alternate", "name_ru": "Поочерёдный подъём гантелей", "name_en": "Alternating Dumbbell Curl",
     "muscle": "biceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0179/0179.gif",
     "instructions": ["Поочерёдно сгибай руки", "В верхней точке разворачивай ладонь"],
     "tips": ["Полная амплитуда важнее веса"]},

    {"code": "curl_hammer", "name_ru": "Молотки", "name_en": "Hammer Curl",
     "muscle": "biceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0269/0269.gif",
     "instructions": ["Нейтральный хват (ладони смотрят друг на друга)", "Сгибай руки"],
     "tips": ["Нагружает брахиалис — придаёт толщину руке"]},

    {"code": "curl_preacher", "name_ru": "Подъём на бицепс (скамья Скотта)", "name_en": "Preacher Curl",
     "muscle": "biceps", "equipment": "barbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0441/0441.gif",
     "instructions": ["Локти на подушке", "Сгибай полностью"],
     "tips": ["Изолирует нижнюю часть бицепса"]},

    {"code": "curl_cable", "name_ru": "Подъём на бицепс у блока", "name_en": "Cable Curl",
     "muscle": "biceps", "equipment": "cable", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0136/0136.gif",
     "instructions": ["Нижний блок", "Сгибай руки к плечам"],
     "tips": ["Постоянное натяжение на всей амплитуде"]},

    {"code": "curl_concentration", "name_ru": "Концентрированные сгибания", "name_en": "Concentration Curl",
     "muscle": "biceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0146/0146.gif",
     "instructions": ["Сидя, локоть упирается во внутреннюю сторону бедра", "Медленное сгибание"],
     "tips": ["Пик нагрузки в верхней точке"]},

    # ─── Трицепс ─────────────────────────────────────────────────
    {"code": "tricep_pushdown_bar", "name_ru": "Жим блока вниз (прямой гриф)", "name_en": "Tricep Pushdown Bar",
     "muscle": "triceps", "equipment": "cable", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0621/0621.gif",
     "instructions": ["Верхний блок", "Прижми локти к бокам", "Разогни руки вниз до конца"],
     "tips": ["Задержись в нижней точке"]},

    {"code": "tricep_pushdown_rope", "name_ru": "Жим каната вниз", "name_en": "Tricep Rope Pushdown",
     "muscle": "triceps", "equipment": "cable", "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0622/0622.gif",
     "instructions": ["Канат", "В нижней точке разводи концы в стороны"],
     "tips": ["Большая амплитуда чем с прямым грифом"]},

    {"code": "skull_crusher", "name_ru": "Французский жим лёжа", "name_en": "Skull Crusher",
     "muscle": "triceps", "equipment": "barbell", "type": "isolation", "difficulty": 3,
     "met_value": 4.0, "gif_url": _GIF + "0561/0561.gif",
     "instructions": ["Лёжа на скамье", "Гриф опускается ко лбу", "Разгибай руки"],
     "tips": ["Длинная головка трицепса"]},

    {"code": "overhead_tricep_ext", "name_ru": "Разгибание трицепса над головой", "name_en": "Overhead Tricep Extension",
     "muscle": "triceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0432/0432.gif",
     "instructions": ["Гантель над головой обеими руками", "Опусти за голову", "Разогни"],
     "tips": ["Лучшее растяжение длинной головки"]},

    {"code": "close_grip_bench", "name_ru": "Жим узким хватом", "name_en": "Close-Grip Bench Press",
     "muscle": "triceps", "equipment": "barbell", "type": "compound", "difficulty": 3,
     "met_value": 5.5, "gif_url": _GIF + "0088/0088.gif",
     "instructions": ["Хват чуть уже плеч", "Жим как обычно"],
     "tips": ["Также нагружает грудь"]},

    {"code": "tricep_kickback", "name_ru": "Разгибание трицепса в наклоне", "name_en": "Tricep Kickback",
     "muscle": "triceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
     "met_value": 3.5, "gif_url": _GIF + "0616/0616.gif",
     "instructions": ["Наклон 90°", "Разогни руку назад до конца"],
     "tips": ["Локоть параллельно полу"]},
]

EXERCISES_CORE = [
    {"code": "plank", "name_ru": "Планка", "name_en": "Plank",
     "muscle": "abs", "equipment": None, "type": "compound", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0460/0460.gif",
     "instructions": ["На локтях или прямых руках", "Тело — прямая линия", "Держи 30-60 сек"],
     "tips": ["Не поднимай таз слишком высоко"]},

    {"code": "crunch", "name_ru": "Скручивания", "name_en": "Crunch",
     "muscle": "abs", "equipment": None, "type": "isolation", "difficulty": 1,
     "met_value": 3.5, "gif_url": _GIF + "0145/0145.gif",
     "instructions": ["Лёжа на спине, руки за голову", "Поднимай плечи от пола"],
     "tips": ["Не тяни шею руками"]},

    {"code": "leg_raise_lying", "name_ru": "Подъём ног лёжа", "name_en": "Lying Leg Raise",
     "muscle": "abs", "equipment": None, "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0355/0355.gif",
     "instructions": ["Лёжа на спине", "Подними прямые ноги до 90°", "Медленно опусти"],
     "tips": ["Поясница прижата к полу"]},

    {"code": "hanging_leg_raise", "name_ru": "Подъём ног в висе", "name_en": "Hanging Leg Raise",
     "muscle": "abs", "equipment": "pullup_bar", "type": "compound", "difficulty": 4,
     "met_value": 5.0, "gif_url": _GIF + "0268/0268.gif",
     "instructions": ["Висишь на перекладине", "Подними ноги до 90°"],
     "tips": ["Для максимума — поднимай ноги к перекладине"]},

    {"code": "cable_crunch", "name_ru": "Скручивания на блоке", "name_en": "Cable Crunch",
     "muscle": "abs", "equipment": "cable", "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0103/0103.gif",
     "instructions": ["На коленях, канат держи у лица", "Скручивай корпус вниз"],
     "tips": ["Лучше нагрузка, чем обычные скручивания"]},

    {"code": "ab_wheel", "name_ru": "Ролик для пресса", "name_en": "Ab Wheel Rollout",
     "muscle": "abs", "equipment": "ab_wheel", "type": "compound", "difficulty": 5,
     "met_value": 6.0, "gif_url": _GIF + "0001/0001.gif",
     "instructions": ["На коленях, держи ролик", "Раскатывайся вперёд", "Втягивай пресс при возврате"],
     "tips": ["Одно из лучших упражнений на пресс"]},

    {"code": "russian_twist", "name_ru": "Русские скручивания", "name_en": "Russian Twist",
     "muscle": "obliques", "equipment": None, "type": "isolation", "difficulty": 2,
     "met_value": 4.0, "gif_url": _GIF + "0517/0517.gif",
     "instructions": ["Сидя, ноги подняты", "Поворачивай корпус из стороны в сторону"],
     "tips": ["С весом или без"]},

    {"code": "side_plank", "name_ru": "Боковая планка", "name_en": "Side Plank",
     "muscle": "obliques", "equipment": None, "type": "isolation", "difficulty": 3,
     "met_value": 4.0, "gif_url": _GIF + "0570/0570.gif",
     "instructions": ["На боку, опора на локоть или руку", "Держи тело прямой линией"],
     "tips": ["Ключевое для боковых мышц пресса"]},

    {"code": "bicycle_crunch", "name_ru": "Велосипед", "name_en": "Bicycle Crunch",
     "muscle": "abs", "equipment": None, "type": "isolation", "difficulty": 2,
     "met_value": 4.5, "gif_url": _GIF + "0072/0072.gif",
     "instructions": ["Лёжа на спине", "Поочерёдно касайся локтем противоположного колена"],
     "tips": ["Медленный темп = больше нагрузки"]},
]

EXERCISES_CARDIO = [
    {"code": "jump_rope", "name_ru": "Прыжки со скакалкой", "name_en": "Jump Rope",
     "muscle": "full_body", "equipment": "jump_rope", "type": "cardio", "difficulty": 2,
     "met_value": 12.0, "gif_url": _GIF + "0302/0302.gif",
     "instructions": ["Скачи в ритме", "Кисти вращают скакалку"],
     "tips": ["Интервалы 30 сек работа / 30 отдых"]},

    {"code": "burpee", "name_ru": "Бёрпи", "name_en": "Burpee",
     "muscle": "full_body", "equipment": None, "type": "cardio", "difficulty": 4,
     "met_value": 8.0, "gif_url": _GIF + "0075/0075.gif",
     "instructions": ["Прыжок вверх → упор лёжа → отжимание → встать"],
     "tips": ["Полное бёрпи с отжиманием = максимум калорий"]},

    {"code": "mountain_climber", "name_ru": "Альпинист", "name_en": "Mountain Climber",
     "muscle": "abs", "equipment": None, "type": "cardio", "difficulty": 3,
     "met_value": 8.0, "gif_url": _GIF + "0415/0415.gif",
     "instructions": ["В положении планки", "Поочерёдно подтягивай колени к груди"],
     "tips": ["Быстрый темп = кардио, медленный = пресс"]},

    {"code": "box_jump", "name_ru": "Запрыгивания на тумбу", "name_en": "Box Jump",
     "muscle": "quads", "equipment": "box", "type": "cardio", "difficulty": 3,
     "met_value": 10.0, "gif_url": _GIF + "0080/0080.gif",
     "instructions": ["Стой перед тумбой", "Мощный прыжок", "Мягко приземлись"],
     "tips": ["Взрывная сила ног"]},

    {"code": "kettlebell_swing", "name_ru": "Махи гири", "name_en": "Kettlebell Swing",
     "muscle": "full_body", "equipment": "kettlebell", "type": "compound", "difficulty": 3,
     "met_value": 9.0, "gif_url": _GIF + "0305/0305.gif",
     "instructions": ["Ноги шире плеч", "Наклон + замах между ног", "Резко выпрями бёдра"],
     "tips": ["Движение от бёдер, не от рук"]},
]

# All extra exercises combined
ALL_EXTRA_EXERCISES = (
    EXERCISES_LEGS +
    EXERCISES_BACK_ADVANCED +
    EXERCISES_CHEST_ADVANCED +
    EXERCISES_SHOULDERS +
    EXERCISES_ARMS +
    EXERCISES_CORE +
    EXERCISES_CARDIO
)
