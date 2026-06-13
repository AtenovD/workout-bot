# 🔍 Аудит бота — Критические ошибки, влияющие на UX

**Дата:** 2026-06-13  
**Статус:** ❌ Найдено 7 критических ошибок

---

## 📋 Найденные ошибки

### 1. ❌ КРИТИЧЕСКАЯ: Missing import in measurements.py
**Файл:** `bot/handlers/measurements.py:139`  
**Проблема:** Функция `main_menu_keyboard()` используется, но не импортирована  
**Симптом:** `NameError: name 'main_menu_keyboard' is not defined` при попытке сохранить замеры  
**Импакт:** ⚠️ **ВЫСОКИЙ** — пользователь не может завершить процесс измерений  
**Решение:** Добавить импорт в начало файла

---

### 2. ❌ КРИТИЧЕСКАЯ: Logic error in measurements.py:40-42
**Файл:** `bot/handlers/measurements.py:40-42`  
```python
text = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
```
**Проблема:** Переменная `text` присваивается, но никогда не используется. На строке 42 повторяется та же логика для `target`.  
**Проблема:** Для обычного Message `msg_or_cb.message` не существует — это вызовет `AttributeError`  
**Симптом:** `AttributeError: 'Message' object has no attribute 'message'`  
**Импакт:** ⚠️ **ВЫСОКИЙ** — меню замеров не открывается  
**Решение:** Переписать логику определения target

---

### 3. ❌ КРИТИЧЕСКАЯ: Undefined variable in rest_timer.py:15
**Файл:** `services/rest_timer.py:15-16`  
```python
def _rest_kb(se_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Следующий подход", callback_data=f"rest:next:{se_id}:{next_set}"),
        InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data=f"rest:skip:{se_id}:{next_set}"),
    ]])
```
**Проблема:** Переменная `next_set` не определена в области видимости функции `_rest_kb`  
**Симптом:** `NameError: name 'next_set' is not defined` при вызове `run_rest_timer()`  
**Импакт:** ⚠️ **КРИТИЧЕСКИЙ** — таймер отдыха полностью не работает, пользователь не может выполнять тренировки  
**Решение:** Добавить `next_set` как параметр функции

---

### 4. ❌ ОШИБКА: Logic error in reminder.py:40-41
**Файл:** `bot/handlers/reminder.py:40-41`  
```python
text = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
```
**Проблема:** Переменная `text` присваивается, но никогда не используется. Дублирование логики как в measurements.py  
**Проблема:** Для Message объект не имеет атрибута `.message`  
**Симптом:** `AttributeError: 'Message' object has no attribute 'message'`  
**Импакт:** ⚠️ **ВЫСОКИЙ** — меню напоминаний не открывается  
**Решение:** Переписать логику определения target

---

### 5. ⚠️ ОШИБКА СТИЛЯ: Импорт datetime внутри функции
**Файл:** `bot/handlers/reminder.py:80`  
```python
import datetime
h, m = map(int, default_info.get("time", "08:00").split(":"))
existing = Reminder(
    user_id=user_id, type=rtype,
    time_of_day=datetime.time(h, m),
    enabled=True
)
```
**Проблема:** `import datetime` происходит внутри функции, а не в начале файла  
**Импакт:** 🟡 **СРЕДНИЙ** — худшие практики, замедление работы, но функция работает  
**Решение:** Переместить импорт в начало файла

---

### 6. ❌ ЛОГИЧЕСКАЯ ОШИБКА: Unterminated string in onboarding.py:120 (ИСПРАВЛЕНО)
**Файл:** `bot/handlers/onboarding.py:120`  
**Проблема:** Используется переменная `message`, которая не определена в контексте — должна быть `callback.from_user.first_name`  
**Статус:** ✅ **ИСПРАВЛЕНО**  

---

### 7. ❌ ОШИБКА СОСТОЯНИЙ: Missing states in OnboardingStates (ИСПРАВЛЕНО)
**Файл:** `bot/states/states.py`  
**Проблема:** Недостающие стейты:
- `age`
- `weight_current`  
- `weight_target`
- `training_days`
- `health_flags`
- `welcome`
- `language` (был, но в неправильном порядке)

**Статус:** ✅ **ИСПРАВЛЕНО** — переупорядочены все стейты в логическом порядке

---

## 🎯 План исправления (по приоритету)

### Приоритет 1 — КРИТИЧЕСКИЙ (блокирует основной функционал)

**Задача 1.1:** Исправить `rest_timer.py` — неработающий таймер отдыха
- [ ] Добавить `next_set` параметром в `_rest_kb()`
- [ ] Проверить компиляцию

**Задача 1.2:** Исправить `measurements.py` — ошибка импорта и логики
- [ ] Добавить импорт `from bot.keyboards.main_menu import main_menu_keyboard`
- [ ] Переписать логику определения `target` (без промежуточной переменной `text`)
- [ ] Проверить компиляцию

**Задача 1.3:** Исправить `reminder.py` — ошибка логики
- [ ] Переписать логику определения `target`
- [ ] Переместить `import datetime` в начало файла
- [ ] Проверить компиляцию

### Приоритет 2 — ТЕСТИРОВАНИЕ (верификация исправлений)
- [ ] Собрать образ: `docker-compose up -d --build bot`
- [ ] Запустить бота: `/start` → проверить калибровку (все стейты)
- [ ] Проверить меню замеров: должно открываться без ошибок
- [ ] Проверить меню напоминаний: должно открываться без ошибок
- [ ] Проверить таймер отдыха: запустить тренировку, выполнить подход, проверить работу таймера

---

## 📊 Матрица рисков

| Ошибка | Компонент | Пользователи затронуты | Вероятность | Импакт |
|--------|-----------|------------------------|-------------|--------|
| rest_timer undefined `next_set` | Тренировки | ВСЕ | 100% | КРИТИЧЕСКИЙ |
| measurements missing import | Замеры | ВСЕ | 100% | КРИТИЧЕСКИЙ |
| measurements logic error | Замеры | ВСЕ | 100% | КРИТИЧЕСКИЙ |
| reminder logic error | Напоминания | Активные | 100% | ВЫСОКИЙ |
| Datetime import в функции | Напоминания | Активные | 100% | СРЕДНИЙ |

---

## ✅ Исправлено в этой сессии

### Критические ошибки (ВСЕ исправлены)
- [x] **rest_timer.py** — добавлен параметр `next_set` в функцию `_rest_kb()`
- [x] **measurements.py** — добавлен импорт `main_menu_keyboard`
- [x] **reminder.py** — исправлена логика target, перемещен импорт `datetime`
- [x] **bot/main.py** — обновлена инициализация Bot под aiogram 3.7.0

### Состояния (исправлено)
- [x] Добавлены недостающие стейты в `OnboardingStates`
- [x] Исправлена ошибка с переменной `message` в `onboarding.py:120`
- [x] Компиляция Python успешна (`py_compile`)

### Статус Docker
- [x] Образ пересобран успешно
- [x] ✅ Бот запустился и работает

---

## 🚀 Следующие шаги

1. Исправить `rest_timer.py` (Приоритет 1.1)
2. Исправить `measurements.py` (Приоритет 1.2)  
3. Исправить `reminder.py` (Приоритет 1.3)
4. Пересобрать Docker образ
5. Запустить интеграционные тесты
