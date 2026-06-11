"""
Calories burned calculator using MET values.
Formula: Calories = MET * weight_kg * hours
"""

DEFAULT_MET = {
    "compound": 6.0,
    "isolation": 4.0,
    "cardio": 8.0,
    "mobility": 2.5,
}


def calculate_calories_burned(met: float, body_weight_kg: float, duration_min: int) -> int:
    """
    Calculate calories burned during workout.
    
    Args:
        met: MET value for activity type
        body_weight_kg: User's body weight in kg
        duration_min: Duration in minutes
    
    Returns:
        Calories burned (kcal) as integer
    """
    hours = duration_min / 60.0
    calories = met * body_weight_kg * hours
    return max(1, round(calories))


def estimate_workout_calories(
    exercises: list[dict],
    body_weight_kg: float,
    duration_min: int,
) -> int:
    """
    Estimate total calories for a workout session.
    Uses weighted average of MET values.
    """
    if not exercises:
        return calculate_calories_burned(DEFAULT_MET["compound"], body_weight_kg, duration_min)
    
    total_met = sum(e.get("met", DEFAULT_MET["compound"]) for e in exercises)
    avg_met = total_met / len(exercises)
    return calculate_calories_burned(avg_met, body_weight_kg, duration_min)
