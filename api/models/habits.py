"""
Pydantic models for Daily Habits Tracker.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# ============== Exercise Models ==============

class ExerciseEntry(BaseModel):
    """Single exercise entry."""
    exercise_type: str  # 'hip_exercises', 'upper_body', 'walk', 'yoga', 'eye_exercises', 'meditation', 'cardio'
    completed: bool = False
    duration_minutes: Optional[int] = None
    reps: Optional[int] = None
    notes: Optional[str] = None

class ExerciseEntryResponse(ExerciseEntry):
    """Exercise entry with ID."""
    id: int

# ============== Meal Models ==============

class MealEntry(BaseModel):
    """Single meal entry."""
    meal_type: str  # 'breakfast', 'lunch', 'evening_snack', 'dinner', 'night_snack'
    completed: bool = False
    quality: Optional[str] = None  # 'healthy', 'moderate', 'unhealthy'
    portion_size: Optional[str] = None  # 'small', 'medium', 'large'
    has_protein: bool = False
    notes: Optional[str] = None  # what specifically you ate

class MealEntryResponse(MealEntry):
    """Meal entry with ID."""
    id: int

# ============== Sleep Models ==============

class SleepEntry(BaseModel):
    """Sleep tracking entry."""
    completed: bool = False
    hours: float = Field(default=0, ge=0, le=24)
    quality: Optional[str] = None  # 'Good', 'Ok', 'Bad'
    energy: Optional[str] = None   # 'Fresh', 'Normal', 'Tired'

class SleepEntryResponse(SleepEntry):
    """Sleep entry with ID."""
    id: int

# ============== Daily Log Models ==============

class DailyLogCreate(BaseModel):
    """Request model for creating/updating a daily log."""
    log_date: date
    exercises: List[ExerciseEntry] = Field(default_factory=list)
    meals: List[MealEntry] = Field(default_factory=list)
    water_glasses: int = Field(default=0, ge=0, le=20)
    sleep: Optional[SleepEntry] = None

class DailyLogResponse(BaseModel):
    """Response model for a daily log."""
    id: int
    user_id: int
    log_date: date
    exercises: List[ExerciseEntryResponse] = Field(default_factory=list)
    meals: List[MealEntryResponse] = Field(default_factory=list)
    water_glasses: int = 0
    sleep: Optional[SleepEntryResponse] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Computed fields for quick stats
    exercise_score: int = 0  # Number of completed exercises
    meal_score: int = 0      # Number of healthy meals
    total_score: int = 0     # Overall daily score (0-100)

class DailyLogListResponse(BaseModel):
    """Response model for list of daily logs."""
    logs: List[DailyLogResponse]
    total: int

# ============== Stats/Reports Models ==============

class WeeklyStats(BaseModel):
    """Weekly statistics."""
    week_start: date
    week_end: date
    days_logged: int
    total_exercises_completed: int
    total_healthy_meals: int
    average_water_glasses: float
    average_daily_score: float
    current_streak: int
    best_streak: int

class MonthlyStats(BaseModel):
    """Monthly statistics."""
    month: str  # "2026-01"
    days_logged: int
    total_exercises_completed: int
    total_healthy_meals: int
    average_water_glasses: float
    average_daily_score: float
    exercise_breakdown: dict  # {'walk': 15, 'gym': 10, ...}
    meal_quality_breakdown: dict  # {'healthy': 40, 'moderate': 20, 'unhealthy': 5}

class StreakInfo(BaseModel):
    """Streak information."""
    current_streak: int
    best_streak: int
    last_logged_date: Optional[date] = None
