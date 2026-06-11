from aiogram.fsm.state import State, StatesGroup


class CalibrationStates(StatesGroup):
    welcome = State()
    gender = State()
    age = State()
    height = State()
    weight_current = State()
    weight_target = State()
    goal = State()
    experience = State()
    health_flags = State()
    equipment = State()
    training_days = State()
    duration = State()
    summary = State()


class WorkoutStates(StatesGroup):
    choosing_type = State()
    choosing_modifier = State()
    overview = State()
    exercise_intro = State()
    logging_set = State()
    rest_timer = State()
    exercise_done = State()
    session_complete = State()


class EquipmentStates(StatesGroup):
    browsing = State()


class ProgressStates(StatesGroup):
    menu = State()
    add_measurement = State()


class ScheduleStates(StatesGroup):
    setup = State()
    choose_days = State()
    choose_time = State()
    choose_timezone = State()
