"""Exercises seed data — part 3: New 40 exercises (forearms, TRX, bands, kettlebell, mobility, bodyweight, rear_delt, cable, HIIT)"""

EXERCISES_NEW = [
    # ═══════════════════════════════════════════
    # FOREARMS / GRIP (3 упражнения)
    # ═══════════════════════════════════════════
    {"code": "wrist_roller", "name_ru": "Вращение роллера для запястий", "name_en": "Wrist Roller",
     "muscle": "forearms", "equipment": "Other", "eq_cat": "stationary", "type": "isolation", "difficulty": 1,
     "met": 3.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Wrist_Roller/Wrist_Roller.gif",
     "instructions": ["Держи роллер на вытянутых руках", "Накручивай трос вращением кисти вперёд", "Раскручивай в обратном направлении"]},
    {"code": "reverse_barbell_curl", "name_ru": "Обратные сгибания со штангой", "name_en": "Reverse Barbell Curl",
     "muscle": "forearms", "equipment": "Barbell", "eq_cat": "stationary", "type": "isolation", "difficulty": 2,
     "met": 4.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Reverse_Barbell_Curl/Reverse_Barbell_Curl.gif",
     "instructions": ["Хват сверху (пронация), штанга на вытянутых руках", "Сгибай руки до 90°", "Медленно опускай"]},
    {"code": "dead_hang", "name_ru": "Вис на перекладине", "name_en": "Dead Hang",
     "muscle": "forearms", "equipment": "Body Only", "eq_cat": "stationary", "type": "isolation", "difficulty": 1,
     "met": 3.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Dead_Hang/Dead_Hang.gif",
     "instructions": ["Повиснуть на перекладине прямым хватом", "Плечи чуть в стороны, не пожимать", "Удерживать позицию 20–60 секунд"]},

    # ═══════════════════════════════════════════
    # TRX / ПЕТЛИ (4 упражнения) — нет GIF в базе, используем ближайшие аналоги
    # ═══════════════════════════════════════════
    {"code": "trx_row", "name_ru": "Тяга в TRX", "name_en": "TRX Row",
     "muscle": "back", "equipment": "Other", "eq_cat": "portable", "type": "compound", "difficulty": 2,
     "met": 5.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Inverted_Row_with_Straps/Inverted_Row_with_Straps.gif",
     "instructions": ["Держись за ручки TRX, тело прямое под углом", "Тяни грудь к рукоятям, сводя лопатки", "Медленно выпрямляй руки"]},
    {"code": "trx_pushup", "name_ru": "Отжимания в TRX", "name_en": "TRX Push-Up",
     "muscle": "chest", "equipment": "Other", "eq_cat": "portable", "type": "compound", "difficulty": 3,
     "met": 5.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Push-Up/Push-Up.gif",
     "instructions": ["Ноги в петлях TRX, упор на ладони", "Опускай грудь к полу, держа тело прямым", "Отжимайся в исходное положение"]},
    {"code": "trx_squat", "name_ru": "Приседания в TRX", "name_en": "TRX Squat",
     "muscle": "legs", "equipment": "Other", "eq_cat": "portable", "type": "compound", "difficulty": 1,
     "met": 5.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Bodyweight_Squat/Bodyweight_Squat.gif",
     "instructions": ["Держись за ручки TRX, стопы на ширине плеч", "Приседай до параллели бёдер с полом", "Вставай, разгибая ноги"]},
    {"code": "trx_plank", "name_ru": "Планка в TRX", "name_en": "TRX Plank",
     "muscle": "abs", "equipment": "Other", "eq_cat": "portable", "type": "isolation", "difficulty": 3,
     "met": 4.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Plank/Plank.gif",
     "instructions": ["Ноги в петлях, упор на предплечья", "Держи тело прямым, не опуская таз", "Удерживай 20–45 секунд"]},

    # ═══════════════════════════════════════════
    # РЕЗИНКИ / RESISTANCE BAND (4 упражнения)
    # ═══════════════════════════════════════════
    {"code": "band_pull_apart", "name_ru": "Разведение резинки перед собой", "name_en": "Band Pull Apart",
     "muscle": "shoulders", "equipment": "Bands", "eq_cat": "portable", "type": "isolation", "difficulty": 1,
     "met": 3.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Band_Pull_Apart/Band_Pull_Apart.gif",
     "instructions": ["Держи резинку на ширине плеч прямыми руками", "Разводи руки в стороны до касания груди", "Медленно возвращай"]},
    {"code": "band_squat", "name_ru": "Приседания с резинкой", "name_en": "Band Squat",
     "muscle": "legs", "equipment": "Bands", "eq_cat": "portable", "type": "compound", "difficulty": 1,
     "met": 5.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Calf_Raises_-_With_Bands/Calf_Raises_-_With_Bands.gif",
     "instructions": ["Встань на резинку, концы в руках на плечах", "Приседай до параллели", "Вставай, выталкивая колени наружу"]},
    {"code": "band_good_morning", "name_ru": "Гуд-морнинг с резинкой", "name_en": "Band Good Morning",
     "muscle": "back", "equipment": "Bands", "eq_cat": "portable", "type": "compound", "difficulty": 2,
     "met": 4.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Band_Good_Morning_Pull_Through/Band_Good_Morning_Pull_Through.gif",
     "instructions": ["Встань на резинку, конец закинь на плечи", "Наклоняйся вперёд, сохраняя спину прямой", "Разгибайся усилием ягодиц и хамстрингов"]},
    {"code": "band_curl", "name_ru": "Сгибания рук с резинкой", "name_en": "Band Curl",
     "muscle": "biceps", "equipment": "Bands", "eq_cat": "portable", "type": "isolation", "difficulty": 1,
     "met": 3.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Resistance_Band_Curls/Resistance_Band_Curls.gif",
     "instructions": ["Встань на резинку, концы в кулаках", "Сгибай руки до плеч", "Медленно опускай"]},

    # ═══════════════════════════════════════════
    # ГИРИ / KETTLEBELL (3 упражнения)
    # ═══════════════════════════════════════════
    {"code": "kettlebell_swing", "name_ru": "Махи гирей", "name_en": "Kettlebell Swing",
     "muscle": "glutes", "equipment": "Kettlebells", "eq_cat": "stationary", "type": "compound", "difficulty": 2,
     "met": 9.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Double_Kettlebell_Swing/Double_Kettlebell_Swing.gif",
     "instructions": ["Ноги шире плеч, гиря между ног", "Толчок бёдрами — гиря летит до уровня плеч", "Контролируй опускание, снова уходи в наклон"]},
    {"code": "kettlebell_windmill", "name_ru": "Мельница с гирей", "name_en": "Kettlebell Windmill",
     "muscle": "shoulders", "equipment": "Kettlebells", "eq_cat": "stationary", "type": "compound", "difficulty": 3,
     "met": 6.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Advanced_Kettlebell_Windmill/Advanced_Kettlebell_Windmill.gif",
     "instructions": ["Жим гири над головой одной рукой", "Наклоняйся в сторону, другой рукой тянись к полу", "Возвращайся медленно"]},
    {"code": "kettlebell_row", "name_ru": "Тяга гири в наклоне", "name_en": "Kettlebell Row",
     "muscle": "back", "equipment": "Kettlebells", "eq_cat": "stationary", "type": "compound", "difficulty": 2,
     "met": 5.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Alternating_Kettlebell_Row/Alternating_Kettlebell_Row.gif",
     "instructions": ["Наклон вперёд, спина прямая", "Тяни гирю к поясу, локоть вдоль корпуса", "Опускай с контролем"]},

    # ═══════════════════════════════════════════
    # MOBILITY / РАЗМИНКА (4 упражнения)
    # ═══════════════════════════════════════════
    {"code": "ankle_circles", "name_ru": "Круговые движения голеностопом", "name_en": "Ankle Circles",
     "muscle": "calves", "equipment": "Body Only", "eq_cat": "none", "type": "mobility", "difficulty": 1,
     "met": 2.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Ankle_Circles/Ankle_Circles.gif",
     "instructions": ["Приподними ногу", "Делай медленные круги стопой 10 раз по часовой", "Повтори против часовой"]},
    {"code": "hip_90_90_stretch", "name_ru": "Растяжка 90/90 для бёдер", "name_en": "90/90 Hip Stretch",
     "muscle": "glutes", "equipment": "Body Only", "eq_cat": "none", "type": "mobility", "difficulty": 1,
     "met": 2.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/90_90_Hamstring/90_90_Hamstring.gif",
     "instructions": ["Сядь в позу 90/90: оба колена под прямым углом", "Наклоняйся вперёд к передней ноге", "Удерживай 30–45 секунд"]},
    {"code": "cat_cow_stretch", "name_ru": "Кошка-корова", "name_en": "Cat Cow Stretch",
     "muscle": "back", "equipment": "Body Only", "eq_cat": "none", "type": "mobility", "difficulty": 1,
     "met": 2.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Cat_Stretch/Cat_Stretch.gif",
     "instructions": ["Упор на ладони и колени", "Вдох — прогнись вниз (корова)", "Выдох — округли спину вверх (кошка)"]},
    {"code": "world_greatest_stretch", "name_ru": "Величайшая растяжка", "name_en": "World Greatest Stretch",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "mobility", "difficulty": 2,
     "met": 3.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Adductor_Stretch/Adductor_Stretch.gif",
     "instructions": ["Шаг вперёд в выпад", "Рукой с той же стороны упри локоть в пол рядом со стопой", "Потянись вращением корпуса вверх"]},

    # ═══════════════════════════════════════════
    # РАСШИРЕННЫЙ BODYWEIGHT (6 упражнений)
    # ═══════════════════════════════════════════
    {"code": "pistol_squat", "name_ru": "Пистолет (приседание на одной ноге)", "name_en": "Pistol Squat",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 5,
     "met": 7.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Bodyweight_Squat/Bodyweight_Squat.gif",
     "instructions": ["Стоя на одной ноге, вторую вытяни вперёд", "Медленно приседай до самого низа", "Разгибай опорную ногу и вставай"]},
    {"code": "pike_pushup", "name_ru": "Отжимания из пики", "name_en": "Pike Push-Up",
     "muscle": "shoulders", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 5.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Pike_Push-up/Pike_Push-up.gif",
     "instructions": ["Позиция перевёрнутой V (таз высоко)", "Сгибай руки, опуская голову к полу", "Отжимайся вверх, не опуская таз"]},
    {"code": "dragon_flag", "name_ru": "Флаг дракона", "name_en": "Dragon Flag",
     "muscle": "abs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 5,
     "met": 8.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Dragon_Flag/Dragon_Flag.gif",
     "instructions": ["Лёжа, держись за скамью за головой", "Подними тело прямым — опора только на плечи", "Медленно опускай, не касаясь пола"]},
    {"code": "archer_pushup", "name_ru": "Лучник (асимметричные отжимания)", "name_en": "Archer Push-Up",
     "muscle": "chest", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 4,
     "met": 6.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Push-Up/Push-Up.gif",
     "instructions": ["Широкая стойка, руки широко", "Сгибай одну руку — тяни грудь к ней, вторая прямая", "Чередуй стороны"]},
    {"code": "tuck_jump", "name_ru": "Прыжок с подтягиванием колен", "name_en": "Tuck Jump",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 9.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Tuck_Jump/Tuck_Jump.gif",
     "instructions": ["Стоя, сделай взрывной прыжок вверх", "В верхней точке подтяни колени к груди", "Мягко приземлись на носки"]},
    {"code": "diamond_pushup", "name_ru": "Алмазные отжимания", "name_en": "Diamond Push-Up",
     "muscle": "triceps", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 5.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Diamond_Push-Up/Diamond_Push-Up.gif",
     "instructions": ["Руки под грудью, большие и указательные пальцы образуют ромб", "Опускай грудь к рукам", "Отжимайся, удерживая локти у тела"]},

    # ═══════════════════════════════════════════
    # ЗАДНЯЯ ДЕЛЬТА / REAR DELTS (3 упражнения)
    # ═══════════════════════════════════════════
    {"code": "face_pull", "name_ru": "Тяга к лицу в кроссовере", "name_en": "Face Pull",
     "muscle": "shoulders", "equipment": "Cable", "eq_cat": "stationary", "type": "isolation", "difficulty": 2,
     "met": 4.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Face_Pull/Face_Pull.gif",
     "instructions": ["Трос на уровне лица, хват нейтральный", "Тяни к ушам, разводя локти в стороны", "Медленно возвращай"]},
    {"code": "cable_rear_delt_fly", "name_ru": "Разведение в кроссовере на заднюю дельту", "name_en": "Cable Rear Delt Fly",
     "muscle": "shoulders", "equipment": "Cable", "eq_cat": "stationary", "type": "isolation", "difficulty": 2,
     "met": 4.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Cable_Rear_Delt_Fly/Cable_Rear_Delt_Fly.gif",
     "instructions": ["Тросы крест-накрест, наклон вперёд", "Разводи руки в стороны, не сгибая локти", "Контролируй обратное движение"]},
    {"code": "bent_over_rear_delt_raise", "name_ru": "Разведение гантелей в наклоне (задняя дельта)", "name_en": "Bent-Over Rear Delt Raise",
     "muscle": "shoulders", "equipment": "Dumbbell", "eq_cat": "stationary", "type": "isolation", "difficulty": 2,
     "met": 4.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Bent_Over_Dumbbell_Rear_Deltoid_Raise_With_Head_On_Bench/Bent_Over_Dumbbell_Rear_Deltoid_Raise_With_Head_On_Bench.gif",
     "instructions": ["Наклон вперёд, спина прямая, гантели вниз", "Разводи руки в стороны до уровня плеч", "Удерживай 1 сек, медленно опускай"]},

    # ═══════════════════════════════════════════
    # КАБЕЛЬНЫЕ (3 упражнения)
    # ═══════════════════════════════════════════
    {"code": "cable_woodchop", "name_ru": "Вращение корпуса с тросом (дровосек)", "name_en": "Cable Woodchop",
     "muscle": "abs", "equipment": "Cable", "eq_cat": "stationary", "type": "compound", "difficulty": 3,
     "met": 5.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Cable_Woodchoppers_(up_to_low)/Cable_Woodchoppers_(up_to_low).gif",
     "instructions": ["Трос сверху сбоку, встань боком к блоку", "Тяни по диагонали сверху-вниз, вращая корпус", "Возвращай с контролем"]},
    {"code": "cable_pull_through", "name_ru": "Протяжка через ноги (кабельная)", "name_en": "Cable Pull-Through",
     "muscle": "glutes", "equipment": "Cable", "eq_cat": "stationary", "type": "compound", "difficulty": 2,
     "met": 5.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Cable_Pull_Through/Cable_Pull_Through.gif",
     "instructions": ["Трос снизу, стоишь спиной к стойке, хват между ног", "Наклон вперёд с прямой спиной", "Разгибайся бёдрами, тяня трос вперёд"]},
    {"code": "cable_hip_abduction", "name_ru": "Отведение ноги в кроссовере", "name_en": "Cable Hip Abduction",
     "muscle": "glutes", "equipment": "Cable", "eq_cat": "stationary", "type": "isolation", "difficulty": 1,
     "met": 3.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Cable_Hip_Adduction/Cable_Hip_Adduction.gif",
     "instructions": ["Трос на щиколотке, стоишь боком к блоку", "Отводи ногу в сторону, не наклоняя корпус", "Медленно возвращай"]},

    # ═══════════════════════════════════════════
    # HIIT / ПЛИОМЕТРИКА (4 упражнения)
    # ═══════════════════════════════════════════
    {"code": "jump_squat", "name_ru": "Приседания с прыжком", "name_en": "Jump Squat",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 9.5, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Jump_Squat/Jump_Squat.gif",
     "instructions": ["Присядь до параллели", "Взрывной прыжок вверх, руки помогают", "Мягкое приземление — сразу в следующее приседание"]},
    {"code": "lateral_bound", "name_ru": "Боковые прыжки (латеральные скачки)", "name_en": "Lateral Bound",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 9.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Alternate_Leg_Diagonal_Bound/Alternate_Leg_Diagonal_Bound.gif",
     "instructions": ["На одной ноге оттолкнись в сторону", "Приземлись на другую ногу, мягко", "Чередуй стороны в быстром темпе"]},
    {"code": "broad_jump", "name_ru": "Прыжок в длину с места", "name_en": "Broad Jump",
     "muscle": "legs", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 3,
     "met": 9.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Standing_Broad_Jump/Standing_Broad_Jump.gif",
     "instructions": ["Ноги чуть шире плеч, небольшой присед", "Взрывной прыжок вперёд с взмахом рук", "Мягкое приземление на обе ноги"]},
    {"code": "burpee", "name_ru": "Бёрпи", "name_en": "Burpee",
     "muscle": "chest", "equipment": "Body Only", "eq_cat": "none", "type": "compound", "difficulty": 4,
     "met": 11.0, "gif_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Burpee/Burpee.gif",
     "instructions": ["Из стойки — упор лёжа", "Отжимание — подтяни ноги к рукам", "Прыжок вверх с хлопком над головой"]},
]
