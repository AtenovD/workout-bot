"""
Calorie calculation using MET values.
"""


def calculate_calories_burned(
    met_value: float,
    weight_kg: float,
    duration_min: float,
) -> int:
    """
    Formula: Calories = MET * weight_kg * duration_hours
    """
    duration_hours = duration_min / 60
    calories = met_value * weight_kg * duration_hours
    return round(calories)


# Default MET values for exercise categories
DEFAULT_MET = {
    "compound": 6.0,
    "isolation": 4.0,
    "cardio": 8.0,
    "mobility": 2.5,
}
