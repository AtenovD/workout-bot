from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    gender = State()
    birth_date = State()
    height = State()
    current_weight = State()
    target_weight = State()
    goal = State()
    experience = State()
    training_structure = State()
    split_type = State()
    duration = State()
    equipment = State()
    health = State()
    schedule_mode = State()
    schedule_days = State()
    reminder_time = State()


class WorkoutStates(StatesGroup):
    choosing_modifier = State()
    overview = State()
    logging_set = State()
    resting = State()
    replacing_exercise = State()


class ProfileStates(StatesGroup):
    entering_weight = State()
    entering_height = State()


class ScheduleStates(StatesGroup):
    entering_time = State()


class MeasurementStates(StatesGroup):
    entering_weight = State()
    entering_measurements = State()
