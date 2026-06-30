from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    language = State()
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
    strength_calibration = State()


class WorkoutStates(StatesGroup):
    choosing_modifier = State()
    overview = State()
    logging_set = State()
    resting = State()
    replacing_exercise = State()
    in_exercise = State()


class ProfileStates(StatesGroup):
    entering_weight = State()
    entering_height = State()


class ScheduleStates(StatesGroup):
    entering_time = State()


class MeasurementStates(StatesGroup):
    entering_weight = State()
    entering_measurements = State()
