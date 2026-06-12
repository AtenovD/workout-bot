# Bot handlers package
# Note: onboarding.py handles /start and initial calibration flow

from .workout import router as workout_router
from .equipment import router as equipment_router
from .schedule import router as schedule_router
from .profile import router as profile_router
from .calibration import router as calibration_router
from .gamification import router as gamification_router
from .reminder import router as reminder_router
from .measurements import router as measurements_router
from .referral import router as referral_router
from .settings import router as settings_router
from .help import router as help_router
from .admin import router as admin_router

__all__ = [
    "workout_router", "equipment_router", "schedule_router",
    "profile_router", "calibration_router", "gamification_router",
    "reminder_router", "measurements_router", "referral_router",
    "settings_router", "help_router", "admin_router",
]
