from .start import router as start_router
from .workout import router as workout_router
from .equipment import router as equipment_router
from .schedule import router as schedule_router
from .profile import router as profile_router
from .calibration import router as calibration_router
from .gamification import router as gamification_router
from .reminder import router as reminder_router
from .measurements import router as measurements_router
from .referral import router as referral_router

__all__ = [
    "start_router",
    "workout_router",
    "equipment_router",
    "schedule_router",
    "profile_router",
    "calibration_router",
    "gamification_router",
    "reminder_router",
    "measurements_router",
    "referral_router",
]
