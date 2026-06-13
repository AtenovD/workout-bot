"""exercises_new_40.py — 40 новых упражнений.
Закрывают пробелы: TRX, резинки, гири, мобилити, предплечья,
bodyweight-продвинутый, задняя дельта, кабель, HIIT/плиометрика.

GIF source: yuhonas/free-exercise-db (MIT)
Base: https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/
"""

_GIF = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

# ─── FOREARMS / ПРЕДПЛЕЧЬЯ ────────────────────────────────────────────────────
EXERCISES_FOREARMS = [
    {
        "code": "wrist_curl", "name_ru": "Сгибание запястий с гантелью", "name_en": "Dumbbell Wrist Curl",
        "muscle": "forearms", "equipment": "dumbbell", "type": "isolation", "difficulty": 1,
        "met_value": 3.0, "gif_url": _GIF + "0648/0648.gif",
        "description": "Изолированная нагрузка на сгибатели предплечья",
        "instructions": [
            "Сядь, предплечья лежат на бёдрах ладонями вверх",
            "Гантель свисает с кисти",
            "Сгибай запястье вверх максимально",
            "Медленно опусти"
        ],
        "tips": ["Маленький вес, высокие повторы", "Предплечье не отрывается от бедра"],
        "common_mistakes": ["Слишком большой вес", "Движение в локте"]
    },
    {
        "code": "reverse_curl", "name_ru": "Подъём штанги обратным хватом", "name_en": "Reverse Barbell Curl",
        "muscle": "forearms", "equipment": "barbell", "type": "isolation", "difficulty": 2,
        "met_value": 3.5, "gif_url": _GIF + "0490/0490.gif",
        "description": "Нагружает плечелучевую мышцу и разгибатели предплечья",
        "instructions": [
            "Хват сверху (пронация) на ширине плеч",
            "Локти прижаты к туловищу",
            "Сгибай руки до плеч",
            "Медленно опусти"
        ],
        "tips": ["Используй ez-гриф чтобы снять нагрузку с запястий"],
        "common_mistakes": ["Помощь корпусом", "Слишком быстрый темп"]
    },
    {
        "code": "farmers_walk", "name_ru": "Фермерская прогулка", "name_en": "Farmer's Walk",
        "muscle": "forearms", "equipment": "dumbbell", "type": "compound", "difficulty": 2,
        "met_value": 5.5, "gif_url": _GIF + "0221/0221.gif",
        "description": "Функциональное упражнение на хват, кор и трапеции",
        "instructions": [
            "Возьми тяжёлые гантели в каждую руку",
            "Иди ровно, плечи назад, пресс напряжён",
            "Шаги равномерные, 20–40 метров"
        ],
        "tips": ["Чем тяжелее, тем лучше для хвата", "Следи за осанкой"],
        "common_mistakes": ["Сутулость", "Слишком короткая дистанция"]
    },
]

# ─── TRX ПЕТЛИ ────────────────────────────────────────────────────────────────
EXERCISES_TRX = [
    {
        "code": "trx_row", "name_ru": "TRX тяга", "name_en": "TRX Row",
        "muscle": "lats", "equipment": "trx", "type": "compound", "difficulty": 2,
        "met_value": 5.0, "gif_url": _GIF + "0526/0526.gif",
        "description": "Горизонтальная тяга с TRX — замена тяги штанги",
        "instructions": [
            "Возьмись за петли, тело под углом 45°",
            "Ноги прямые, тело как доска",
            "Подтягивай грудь к рукоятям",
            "Медленно вытяни руки обратно"
        ],
        "tips": ["Чем ниже тело — тем сложнее", "Лопатки сводятся в верхней точке"],
        "common_mistakes": ["Таз провисает", "Слишком лёгкий угол"]
    },
    {
        "code": "trx_pushup", "name_ru": "TRX отжимания", "name_en": "TRX Push-up",
        "muscle": "chest", "equipment": "trx", "type": "compound", "difficulty": 3,
        "met_value": 5.5, "gif_url": _GIF + "0427/0427.gif",
        "description": "Нестабильность TRX усиливает нагрузку на кор и грудные",
        "instructions": [
            "Возьмись за петли, тело в планке",
            "Опускайся до угла 90° в локтях",
            "Выжмись обратно"
        ],
        "tips": ["Чем дальше петли от стены — тем сложнее"],
        "common_mistakes": ["Провисание таза", "Раскачка петель рывками"]
    },
    {
        "code": "trx_squat", "name_ru": "TRX приседания", "name_en": "TRX Squat",
        "muscle": "quads", "equipment": "trx", "type": "compound", "difficulty": 1,
        "met_value": 5.0, "gif_url": _GIF + "0539/0539.gif",
        "description": "Петли помогают держать баланс при глубоком приседе",
        "instructions": [
            "Держись за петли прямыми руками",
            "Приседай глубоко, держа спину прямо",
            "Поднимайся, помогая руками"
        ],
        "tips": ["Отлично для мобильности голеностопа"],
        "common_mistakes": ["Слишком сильное натяжение петель"]
    },
    {
        "code": "trx_plank", "name_ru": "TRX планка с подтягиванием колен", "name_en": "TRX Knee Tuck",
        "muscle": "abs", "equipment": "trx", "type": "compound", "difficulty": 4,
        "met_value": 5.5, "gif_url": _GIF + "0460/0460.gif",
        "description": "Планка с ногами в петлях — нагрузка на кор и плечи",
        "instructions": [
            "Вставь ноги в петли, встань в планку",
            "Подтяни колени к груди",
            "Вытяни обратно"
        ],
        "tips": ["Пресс напряжён постоянно"],
        "common_mistakes": ["Таз поднимается слишком высоко"]
    },
]

# ─── РЕЗИНКИ / RESISTANCE BAND ────────────────────────────────────────────────
EXERCISES_BAND = [
    {
        "code": "band_pull_apart", "name_ru": "Разведение резинки перед грудью", "name_en": "Band Pull-Apart",
        "muscle": "rear_delts", "equipment": "resistance_band", "type": "isolation", "difficulty": 1,
        "met_value": 3.0, "gif_url": _GIF + "0498/0498.gif",
        "description": "Здоровье плечевых суставов и задние дельты",
        "instructions": [
            "Держи резинку перед собой прямыми руками",
            "Разводи руки в стороны до упора",
            "Медленно вернись"
        ],
        "tips": ["Можно делать ежедневно как разминку", "Лопатки сводятся в конце"],
        "common_mistakes": ["Согнутые локти", "Слишком лёгкая резинка"]
    },
    {
        "code": "band_squat", "name_ru": "Приседания с резинкой", "name_en": "Band Squat",
        "muscle": "quads", "equipment": "resistance_band", "type": "compound", "difficulty": 1,
        "met_value": 4.5, "gif_url": _GIF + "0150/0150.gif",
        "description": "Резинка добавляет нагрузку без штанги",
        "instructions": [
            "Встань на середину резинки",
            "Концы держи у плеч",
            "Присядь до параллели"
        ],
        "tips": ["Резинка увеличивает нагрузку в верхней точке"],
        "common_mistakes": ["Резинка слетает"]
    },
    {
        "code": "band_row", "name_ru": "Тяга резинки к поясу", "name_en": "Band Row",
        "muscle": "middle_back", "equipment": "resistance_band", "type": "compound", "difficulty": 1,
        "met_value": 4.0, "gif_url": _GIF + "0526/0526.gif",
        "description": "Горизонтальная тяга без тренажёра",
        "instructions": [
            "Закрепи резинку за неподвижную опору",
            "Тяни к поясу, сводя лопатки",
            "Медленно вытяни"
        ],
        "tips": ["Постоянное натяжение — плюс резинки", "Локти ближе к телу"],
        "common_mistakes": ["Помощь корпусом", "Рывки"]
    },
    {
        "code": "band_lateral_walk", "name_ru": "Боковые шаги с резинкой", "name_en": "Band Lateral Walk",
        "muscle": "glutes", "equipment": "resistance_band", "type": "isolation", "difficulty": 1,
        "met_value": 4.0, "gif_url": _GIF + "0062/0062.gif",
        "description": "Активация малой и средней ягодичной мышцы",
        "instructions": [
            "Резинка вокруг голеней или колен",
            "Слегка присядь",
            "Делай шаги в сторону, сохраняя натяжение"
        ],
        "tips": ["Незаменимо для активации ягодиц перед тренировкой"],
        "common_mistakes": ["Колени заваливаются внутрь"]
    },
]

# ─── ГИРИ / KETTLEBELL ────────────────────────────────────────────────────────
EXERCISES_KETTLEBELL = [
    {
        "code": "kb_swing", "name_ru": "Махи гири", "name_en": "Kettlebell Swing",
        "muscle": "glutes", "equipment": "kettlebell", "type": "compound", "difficulty": 3,
        "met_value": 9.0, "gif_url": _GIF + "0305/0305.gif",
        "description": "Взрывное упражнение на заднюю цепь и кардио",
        "instructions": [
            "Ноги шире плеч, гиря между ног",
            "Замах назад с наклоном",
            "Резкий разгиб бёдер — гиря летит до уровня плеч",
            "Повтор"
        ],
        "tips": ["Движение от бёдер, не от рук", "Пресс и ягодицы в верхней точке"],
        "common_mistakes": ["Присед вместо шарнира в тазобедренном", "Горбатая спина"]
    },
    {
        "code": "kb_clean_press", "name_ru": "Подъём и жим гири", "name_en": "KB Clean and Press",
        "muscle": "front_delts", "equipment": "kettlebell", "type": "compound", "difficulty": 4,
        "met_value": 7.5, "gif_url": _GIF + "0046/0046.gif",
        "description": "Комплексное упражнение: бёдра + плечи",
        "instructions": [
            "Подними гирю чистым движением к плечу",
            "Без паузы — жим вверх до полного разгибания",
            "Опусти контролируемо"
        ],
        "tips": ["Одно из лучших упражнений для силы и кардио одновременно"],
        "common_mistakes": ["Удар гири по предплечью при подъёме"]
    },
    {
        "code": "kb_turkish_getup", "name_ru": "Турецкий подъём с гирей", "name_en": "Turkish Get-Up",
        "muscle": "full_body", "equipment": "kettlebell", "type": "compound", "difficulty": 5,
        "met_value": 6.0, "gif_url": _GIF + "0631/0631.gif",
        "description": "Элитное функциональное упражнение на всё тело и стабильность",
        "instructions": [
            "Лёжа, гиря в вытянутой руке",
            "Встань пошагово, не опуская руку",
            "Вернись в исходное"
        ],
        "tips": ["Начинай без веса, освой технику", "Взгляд на гирю"],
        "common_mistakes": ["Спешка", "Потеря контроля над плечом"]
    },
]

# ─── МОБИЛИТИ / ПОДВИЖНОСТЬ ───────────────────────────────────────────────────
EXERCISES_MOBILITY = [
    {
        "code": "hip_flexor_stretch", "name_ru": "Растяжка сгибателей бедра", "name_en": "Hip Flexor Stretch",
        "muscle": "full_body", "equipment": None, "type": "mobility", "difficulty": 1,
        "met_value": 2.5, "gif_url": _GIF + "0282/0282.gif",
        "description": "Снимает напряжение от долгого сидения",
        "instructions": [
            "Встань на одно колено (выпад)",
            "Переднюю ногу согни 90°",
            "Таз подай вперёд-вниз",
            "Держи 30–60 сек"
        ],
        "tips": ["Критично для людей, которые много сидят"],
        "common_mistakes": ["Прогиб поясницы"]
    },
    {
        "code": "thoracic_rotation", "name_ru": "Ротация грудного отдела", "name_en": "Thoracic Rotation",
        "muscle": "full_body", "equipment": None, "type": "mobility", "difficulty": 1,
        "met_value": 2.5, "gif_url": _GIF + "0517/0517.gif",
        "description": "Подвижность грудного отдела позвоночника",
        "instructions": [
            "Встань в позицию «четверенька»",
            "Одну руку за голову",
            "Поворачивай грудь и локоть к потолку",
            "10 повторов на каждую сторону"
        ],
        "tips": ["Делай медленно с паузой в крайней точке"],
        "common_mistakes": ["Компенсация из поясницы"]
    },
    {
        "code": "worlds_greatest_stretch", "name_ru": "Лучшее растяжение мира", "name_en": "World's Greatest Stretch",
        "muscle": "full_body", "equipment": None, "type": "mobility", "difficulty": 2,
        "met_value": 3.0, "gif_url": _GIF + "0286/0286.gif",
        "description": "Комплексная разминка всего тела в одном движении",
        "instructions": [
            "Шаг вперёд — выпад",
            "Руку того же бока поставь рядом со стопой",
            "Другую руку потяни вверх с ротацией",
            "Перенеси вес и растяни заднюю ногу"
        ],
        "tips": ["5 повторов на каждую сторону перед тренировкой"],
        "common_mistakes": ["Слишком быстро"]
    },
    {
        "code": "cat_cow", "name_ru": "Кошка-корова", "name_en": "Cat-Cow",
        "muscle": "full_body", "equipment": None, "type": "mobility", "difficulty": 1,
        "met_value": 2.0, "gif_url": _GIF + "0100/0100.gif",
        "description": "Разминка позвоночника — идеально для старта тренировки",
        "instructions": [
            "Встань на четверенька",
            "Выгни спину вверх (кошка) — подбородок к груди",
            "Прогнись вниз (корова) — взгляд вверх",
            "Медленно чередуй"
        ],
        "tips": ["Дыши: вдох на коровью фазу, выдох на кошку"],
        "common_mistakes": ["Слишком быстро — теряется польза"]
    },
]

# ─── ПРОДВИНУТЫЙ BODYWEIGHT ───────────────────────────────────────────────────
EXERCISES_BODYWEIGHT_ADV = [
    {
        "code": "pistol_squat", "name_ru": "Пистолетик", "name_en": "Pistol Squat",
        "muscle": "quads", "equipment": None, "type": "compound", "difficulty": 5,
        "met_value": 6.0, "gif_url": _GIF + "0458/0458.gif",
        "description": "Приседание на одной ноге — предел силы и баланса",
        "instructions": [
            "Стой на одной ноге",
            "Свободную ногу вытяни вперёд",
            "Медленно приседай до конца",
            "Встань"
        ],
        "tips": ["Начинай с ящика или держась за опору"],
        "common_mistakes": ["Заваливание вперёд", "Колено внутрь"]
    },
    {
        "code": "pike_pushup", "name_ru": "Отжимание из позы собаки мордой вниз", "name_en": "Pike Push-up",
        "muscle": "front_delts", "equipment": None, "type": "compound", "difficulty": 3,
        "met_value": 5.0, "gif_url": _GIF + "0453/0453.gif",
        "description": "Вертикальный жим без отягощений",
        "instructions": [
            "Поза «перевёрнутая V»",
            "Голова направлена вниз",
            "Согни локти — лбом к полу",
            "Выжмись обратно"
        ],
        "tips": ["Подготовка к стойке на руках", "Ноги на возвышении = сложнее"],
        "common_mistakes": ["Таз опускается в горизонталь"]
    },
    {
        "code": "superman", "name_ru": "Супермен", "name_en": "Superman",
        "muscle": "lower_back", "equipment": None, "type": "isolation", "difficulty": 1,
        "met_value": 3.0, "gif_url": _GIF + "0582/0582.gif",
        "description": "Укрепление разгибателей позвоночника и ягодиц",
        "instructions": [
            "Лёжа лицом вниз",
            "Одновременно поднимай руки и ноги",
            "Задержи 2 сек",
            "Опусти"
        ],
        "tips": ["Смотри в пол, не вперёд"],
        "common_mistakes": ["Резкие движения"]
    },
    {
        "code": "nordic_curl", "name_ru": "Нордическое сгибание", "name_en": "Nordic Hamstring Curl",
        "muscle": "hamstrings", "equipment": None, "type": "isolation", "difficulty": 5,
        "met_value": 5.0, "gif_url": _GIF + "0420/0420.gif",
        "description": "Самое эффективное упражнение для профилактики травм подколенных сухожилий",
        "instructions": [
            "Зафиксируй ноги за ступени/скамью",
            "Медленно наклоняйся вперёд, держа тело прямым",
            "Руки ловят падение",
            "Подтянись обратно"
        ],
        "tips": ["Начинай с короткой амплитудой — упражнение очень тяжёлое"],
        "common_mistakes": ["Сгибание в бёдрах"]
    },
    {
        "code": "dive_bomber_pushup", "name_ru": "Отжимание пикирующий бомбардировщик", "name_en": "Dive Bomber Push-up",
        "muscle": "chest", "equipment": None, "type": "compound", "difficulty": 4,
        "met_value": 5.5, "gif_url": _GIF + "0170/0170.gif",
        "description": "Сложные отжимания с полной амплитудой и ротацией",
        "instructions": [
            "Начни в позе «собаки мордой вниз»",
            "Нырни вперёд и вниз",
            "Проведи грудью у пола и вынырни вверх",
            "Обратно"
        ],
        "tips": ["Грудные + дельты + трицепс + кор"],
        "common_mistakes": ["Опускание таза в первой фазе"]
    },
    {
        "code": "dead_hang", "name_ru": "Вис на перекладине", "name_en": "Dead Hang",
        "muscle": "forearms", "equipment": "pullup_bar", "type": "mobility", "difficulty": 1,
        "met_value": 2.5, "gif_url": _GIF + "0268/0268.gif",
        "description": "Декомпрессия позвоночника и тренировка хвата",
        "instructions": [
            "Возьмись за перекладину",
            "Расслабь плечи и позвоночник",
            "Вись 30–60 сек"
        ],
        "tips": ["Делай после каждой тренировки на спину"],
        "common_mistakes": ["Напряжённые плечи"]
    },
]

# ─── ЗАДНЯЯ ДЕЛЬТА / REAR DELTS ───────────────────────────────────────────────
EXERCISES_REAR_DELTS = [
    {
        "code": "prone_y_raise", "name_ru": "Подъём рук Y лёжа", "name_en": "Prone Y Raise",
        "muscle": "rear_delts", "equipment": None, "type": "isolation", "difficulty": 2,
        "met_value": 3.0, "gif_url": _GIF + "0461/0461.gif",
        "description": "Укрепление вращательной манжеты и задних дельт",
        "instructions": [
            "Ляг на живот на скамью",
            "Руки образуют форму Y",
            "Поднимай руки вверх-в стороны"
        ],
        "tips": ["Большой палец смотрит вверх", "Лёгкие гантели или без веса"],
        "common_mistakes": ["Слишком большой вес"]
    },
    {
        "code": "chest_supported_row", "name_ru": "Тяга с упором грудью", "name_en": "Chest Supported Row",
        "muscle": "rear_delts", "equipment": "dumbbell", "type": "compound", "difficulty": 2,
        "met_value": 4.5, "gif_url": _GIF + "0201/0201.gif",
        "description": "Исключает читинг спиной, изолирует мышцы спины",
        "instructions": [
            "Ляг грудью на наклонную скамью 45°",
            "Тяни гантели к бёдрам",
            "Лопатки сводятся"
        ],
        "tips": ["Лучший вариант тяги для тех, кто читингует поясницей"],
        "common_mistakes": ["Отрыв груди от скамьи"]
    },
    {
        "code": "band_face_pull", "name_ru": "Тяга резинки к лицу", "name_en": "Band Face Pull",
        "muscle": "rear_delts", "equipment": "resistance_band", "type": "isolation", "difficulty": 1,
        "met_value": 3.5, "gif_url": _GIF + "0224/0224.gif",
        "description": "Здоровье ротаторов плеча без блочного тренажёра",
        "instructions": [
            "Резинка на уровне лица",
            "Тяни к лицу двумя руками",
            "Локти высоко и в стороны"
        ],
        "tips": ["Делай каждую тренировку — страховка плеч"],
        "common_mistakes": ["Локти опущены вниз"]
    },
]

# ─── КАБЕЛЬНЫЕ ────────────────────────────────────────────────────────────────
EXERCISES_CABLE_ADV = [
    {
        "code": "cable_pullthrough", "name_ru": "Тяга блока между ног", "name_en": "Cable Pull-Through",
        "muscle": "glutes", "equipment": "cable", "type": "compound", "difficulty": 2,
        "met_value": 5.0, "gif_url": _GIF + "0102/0102.gif",
        "description": "Тазовый шарнир с постоянным натяжением",
        "instructions": [
            "Встань спиной к нижнему блоку",
            "Трос между ног, нагнись вперёд",
            "Резко разогни бёдра, встань прямо"
        ],
        "tips": ["Движение из бёдер, как в swing гири"],
        "common_mistakes": ["Приседание вместо наклона"]
    },
    {
        "code": "cable_woodchop", "name_ru": "Рубка дров снизу вверх", "name_en": "Cable Woodchop Low to High",
        "muscle": "obliques", "equipment": "cable", "type": "compound", "difficulty": 2,
        "met_value": 4.5, "gif_url": _GIF + "0103/0103.gif",
        "description": "Ротационная нагрузка на косые мышцы живота",
        "instructions": [
            "Нижний блок, встань боком",
            "Потяни трос по диагонали снизу-вверх с поворотом",
            "Руки прямые"
        ],
        "tips": ["Движение идёт от бёдер, не от рук"],
        "common_mistakes": ["Согнутые руки"]
    },
    {
        "code": "cable_lateral_raise_cross", "name_ru": "Крестовые махи в стороны", "name_en": "Cable Lateral Raise Cross",
        "muscle": "side_delts", "equipment": "cable", "type": "isolation", "difficulty": 2,
        "met_value": 3.5, "gif_url": _GIF + "0166/0166.gif",
        "description": "Постоянное натяжение на боковые дельты",
        "instructions": [
            "Нижний блок слева, возьмись правой рукой через тело",
            "Подними руку в сторону"
        ],
        "tips": ["Лучше растяжение чем с гантелью"],
        "common_mistakes": ["Слишком тяжёлый вес — включается трапеция"]
    },
]

# ─── HIIT / ПЛИОМЕТРИКА ───────────────────────────────────────────────────────
EXERCISES_HIIT = [
    {
        "code": "jump_squat", "name_ru": "Прыжковые приседания", "name_en": "Jump Squat",
        "muscle": "quads", "equipment": None, "type": "cardio", "difficulty": 3,
        "met_value": 9.0, "gif_url": _GIF + "0302/0302.gif",
        "description": "Взрывная плиометрика для ног и кардио",
        "instructions": [
            "Присядь до параллели",
            "Мощно оттолкнись и прыгни вверх",
            "Мягко приземлись на носки"
        ],
        "tips": ["Мягкое приземление снижает нагрузку на колени"],
        "common_mistakes": ["Жёсткое приземление на всю стопу"]
    },
    {
        "code": "high_knees", "name_ru": "Бег с высоким подниманием колен", "name_en": "High Knees",
        "muscle": "full_body", "equipment": None, "type": "cardio", "difficulty": 2,
        "met_value": 8.0, "gif_url": _GIF + "0273/0273.gif",
        "description": "Кардио-разминка и нагрузка на кор",
        "instructions": [
            "Бег на месте",
            "Поднимай колени до уровня пояса",
            "Руки работают активно"
        ],
        "tips": ["30 сек работы / 30 отдыха"],
        "common_mistakes": ["Низко поднятые колени"]
    },
    {
        "code": "lateral_bound", "name_ru": "Боковые прыжки", "name_en": "Lateral Bound",
        "muscle": "glutes", "equipment": None, "type": "cardio", "difficulty": 3,
        "met_value": 8.5, "gif_url": _GIF + "0329/0329.gif",
        "description": "Плиометрика для ягодиц и координации",
        "instructions": [
            "Прыгни боком на одну ногу",
            "Мягко приземлись",
            "Прыгни обратно"
        ],
        "tips": ["Отлично для спортивной формы"],
        "common_mistakes": ["Слишком маленькая амплитуда"]
    },
    {
        "code": "skater_jump", "name_ru": "Прыжки конькобежца", "name_en": "Skater Jump",
        "muscle": "glutes", "equipment": None, "type": "cardio", "difficulty": 3,
        "met_value": 9.0, "gif_url": _GIF + "0553/0553.gif",
        "description": "Боковая плиометрика с приземлением на одну ногу",
        "instructions": [
            "Прыжок в сторону на одной ноге",
            "Другую ногу забрось за опорную",
            "Руки делают взмах как у конькобежца"
        ],
        "tips": ["Хорошо для равновесия и кардио одновременно"],
        "common_mistakes": ["Неустойчивое приземление"]
    },
]

# ─── ЕЩЁ 6 — ДОБИТЬ ДО 40 ────────────────────────────────────────────────────
EXERCISES_EXTRA_6 = [
    {
        "code": "step_up", "name_ru": "Зашагивания на тумбу", "name_en": "Step-Up",
        "muscle": "quads", "equipment": "box", "type": "compound", "difficulty": 2,
        "met_value": 5.5, "gif_url": _GIF + "0591/0591.gif",
        "description": "Функциональный односторонний присед",
        "instructions": ["Поставь ногу на тумбу", "Поднимись, выпрямив ногу", "Опустись контролируемо"],
        "tips": ["Толкайся пяткой стоящей ноги"],
        "common_mistakes": ["Отталкивание нижней ногой"]
    },
    {
        "code": "wall_sit", "name_ru": "Статичный присед у стены", "name_en": "Wall Sit",
        "muscle": "quads", "equipment": None, "type": "isolation", "difficulty": 2,
        "met_value": 4.0, "gif_url": _GIF + "0661/0661.gif",
        "description": "Изометрическая нагрузка на квадрицепс",
        "instructions": ["Спина у стены", "Присядь до угла 90° в коленях", "Держи"],
        "tips": ["Цель — 60 сек и выше"],
        "common_mistakes": ["Колени выходят за носки"]
    },
    {
        "code": "incline_db_curl", "name_ru": "Подъём гантелей на бицепс лёжа", "name_en": "Incline Dumbbell Curl",
        "muscle": "biceps", "equipment": "dumbbell", "type": "isolation", "difficulty": 2,
        "met_value": 3.5, "gif_url": _GIF + "0289/0289.gif",
        "description": "Лучшее растяжение длинной головки бицепса",
        "instructions": ["Лёг на наклонную скамью 45°", "Руки свисают вниз", "Сгибай до плеч"],
        "tips": ["Растяжение в нижней точке = максимальный рост"],
        "common_mistakes": ["Слишком быстрое движение"]
    },
    {
        "code": "cable_crunch_kneeling", "name_ru": "Скручивания на блоке стоя на коленях", "name_en": "Kneeling Cable Crunch",
        "muscle": "abs", "equipment": "cable", "type": "isolation", "difficulty": 2,
        "met_value": 4.0, "gif_url": _GIF + "0103/0103.gif",
        "description": "Лучшее упражнение на пресс с отягощением",
        "instructions": ["Встань на колени у блока", "Трос держи у лица", "Скручивайся вниз носом к коленям"],
        "tips": ["Движение от пресса, не от рук"],
        "common_mistakes": ["Тянет руками вместо пресса"]
    },
    {
        "code": "single_leg_rdl", "name_ru": "Румынская тяга на одной ноге", "name_en": "Single-Leg RDL",
        "muscle": "hamstrings", "equipment": "dumbbell", "type": "compound", "difficulty": 4,
        "met_value": 5.5, "gif_url": _GIF + "0556/0556.gif",
        "description": "Баланс + задняя цепь + стабилизаторы",
        "instructions": ["Стой на одной ноге", "Наклоняйся с гантелью", "Спина прямая, свободная нога уходит назад"],
        "tips": ["Отлично выявляет дисбаланс между ногами"],
        "common_mistakes": ["Разворот таза", "Округление спины"]
    },
    {
        "code": "hollow_body_hold", "name_ru": "Полое тело (hollow body)", "name_en": "Hollow Body Hold",
        "muscle": "abs", "equipment": None, "type": "compound", "difficulty": 3,
        "met_value": 4.0, "gif_url": _GIF + "0279/0279.gif",
        "description": "Фундамент гимнастики — максимальная нагрузка на кор",
        "instructions": [
            "Лёжа на спине", "Руки вытяни за голову",
            "Одновременно подними плечи и ноги",
            "Поясница прижата к полу", "Держи"
        ],
        "tips": ["Начни с 10 сек и наращивай"],
        "common_mistakes": ["Отрыв поясницы от пола"]
    },
]

# ─── ИТОГОВЫЙ СПИСОК: 40 УПРАЖНЕНИЙ ──────────────────────────────────────────
EXERCISES_NEW_40 = (
    EXERCISES_FOREARMS +        # 3
    EXERCISES_TRX +             # 4
    EXERCISES_BAND +            # 4
    EXERCISES_KETTLEBELL +      # 3
    EXERCISES_MOBILITY +        # 4
    EXERCISES_BODYWEIGHT_ADV +  # 6
    EXERCISES_REAR_DELTS +      # 3
    EXERCISES_CABLE_ADV +       # 3
    EXERCISES_HIIT +            # 4
    EXERCISES_EXTRA_6           # 6
)  # Итого: 40


if __name__ == "__main__":
    print(f"Total new exercises: {len(EXERCISES_NEW_40)}")
    muscles = {}
    for ex in EXERCISES_NEW_40:
        m = ex.get("muscle", "unknown")
        muscles[m] = muscles.get(m, 0) + 1
    for m, c in sorted(muscles.items()):
        print(f"  {m}: {c}")
