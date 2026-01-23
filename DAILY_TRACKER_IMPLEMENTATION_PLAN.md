# Daily Tracker (Exercise & Food) - Complete Implementation Plan

## Project Context

**Application**: NoteTracker - Personal Knowledge & Task Management
**Tech Stack**:
- **Backend**: FastAPI (Python) with SQLite database
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS
- **State Management**: Zustand + React Query (TanStack Query)
- **Authentication**: Google OAuth with JWT tokens

**Production URL**: http://80.225.231.148.sslip.io/

---

## Feature Overview

A simple daily habit tracker for exercise and food with:
- **Quick checkbox-based entry** - Mark activities as done with optional notes
- **Exercise tracking** (7 types):
  - 🦵 Hip Exercises - with duration/reps
  - 💪 Upper Body - with duration/reps
  - 🚶 Walk - with duration
  - 🧘 Yoga - with duration
  - 👁️ Eye Exercises - with duration/reps
  - 🧘‍♂️ Meditation - with duration
  - 🏃 Cardio - with duration
- **Food tracking** (5 meals):
  - 🍳 Breakfast
  - 🍛 Lunch
  - 🥜 Evening Snack
  - 🍚 Dinner
  - 🍪 Night Snack
  - Each meal tracks: Quality (Healthy/Moderate/Unhealthy), Portion Size (Small/Medium/Large), Protein checkbox, Notes (what you ate)
- **Water intake** - Track glasses of water (target: 8)
- **Reports** - Daily, Weekly, Monthly views with streaks, scores, and charts

---

## Part 1: Database Schema

### File: `api/database.py`

No changes needed - use existing helper functions:
- `execute_query(sql, params)` - SELECT queries
- `execute_insert(sql, params)` - INSERT, returns last row id
- `execute_update(sql, params)` - UPDATE/DELETE, returns affected rows
- `get_record_by_id(table, record_id)` - Get single record

### New Tables to Create

Create a new file `api/init_habits_db.py` to initialize tables, OR add to existing database initialization:

```sql
-- Daily log entry (one per user per date)
CREATE TABLE IF NOT EXISTS daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, log_date)
);

-- Exercise entries
CREATE TABLE IF NOT EXISTS exercise_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_log_id INTEGER NOT NULL,
    exercise_type TEXT NOT NULL,  -- 'hip_exercises', 'upper_body', 'walk', 'yoga', 'eye_exercises', 'meditation', 'cardio'
    completed INTEGER DEFAULT 0,   -- 0 or 1 (boolean)
    duration_minutes INTEGER,      -- duration in minutes
    reps INTEGER,                  -- number of reps (for exercises like hip/upper body)
    notes TEXT,                    -- optional notes
    FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
);

-- Meal entries
CREATE TABLE IF NOT EXISTS meal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_log_id INTEGER NOT NULL,
    meal_type TEXT NOT NULL,       -- 'breakfast', 'lunch', 'evening_snack', 'dinner', 'night_snack'
    completed INTEGER DEFAULT 0,   -- 0 or 1 (boolean)
    quality TEXT,                  -- 'healthy', 'moderate', 'unhealthy'
    portion_size TEXT,             -- 'small', 'medium', 'large'
    has_protein INTEGER DEFAULT 0, -- 0 or 1 (boolean) - did meal have adequate protein?
    notes TEXT,                    -- what specifically you ate
    FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
);

-- Water intake
CREATE TABLE IF NOT EXISTS water_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_log_id INTEGER NOT NULL,
    glasses INTEGER DEFAULT 0,     -- number of glasses (target: 8)
    FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, log_date);
CREATE INDEX IF NOT EXISTS idx_exercise_entries_log ON exercise_entries(daily_log_id);
CREATE INDEX IF NOT EXISTS idx_meal_entries_log ON meal_entries(daily_log_id);
```

### Database Initialization Script

Create file: `api/init_habits_db.py`

```python
"""
Initialize habits tracking database tables.
Run this once to create the tables.
"""

from api.database import get_db_connection

def init_habits_tables():
    """Create habits tracking tables if they don't exist."""

    with get_db_connection() as conn:
        # Daily logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, log_date)
            )
        """)

        # Exercise entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercise_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                exercise_type TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                duration_minutes INTEGER,
                reps INTEGER,
                notes TEXT,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Meal entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                meal_type TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                quality TEXT,
                portion_size TEXT,
                has_protein INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Water entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS water_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                glasses INTEGER DEFAULT 0,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, log_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_exercise_entries_log ON exercise_entries(daily_log_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meal_entries_log ON meal_entries(daily_log_id)")

        print("Habits tables created successfully!")

if __name__ == "__main__":
    init_habits_tables()
```

---

## Part 2: Backend API

### File: `api/models/habits.py` (NEW FILE)

```python
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

# ============== Water Models ==============

class WaterEntry(BaseModel):
    """Water intake entry."""
    glasses: int = Field(default=0, ge=0, le=20)

# ============== Daily Log Models ==============

class DailyLogCreate(BaseModel):
    """Request model for creating/updating a daily log."""
    log_date: date
    exercises: List[ExerciseEntry] = Field(default_factory=list)
    meals: List[MealEntry] = Field(default_factory=list)
    water_glasses: int = Field(default=0, ge=0, le=20)

class DailyLogResponse(BaseModel):
    """Response model for a daily log."""
    id: int
    user_id: int
    log_date: date
    exercises: List[ExerciseEntryResponse] = Field(default_factory=list)
    meals: List[MealEntryResponse] = Field(default_factory=list)
    water_glasses: int = 0
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
```

### File: `api/routers/habits.py` (NEW FILE)

```python
"""
Daily Habits Tracker API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import date, datetime, timedelta

from api.models.habits import (
    DailyLogCreate, DailyLogResponse, DailyLogListResponse,
    ExerciseEntryResponse, MealEntryResponse,
    WeeklyStats, MonthlyStats, StreakInfo
)
from api.database import execute_query, execute_insert, execute_update, get_record_by_id
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/habits", tags=["habits"])

# ============== Constants ==============

EXERCISE_TYPES = ['hip_exercises', 'upper_body', 'walk', 'yoga', 'eye_exercises', 'meditation', 'cardio']
MEAL_TYPES = ['breakfast', 'lunch', 'evening_snack', 'dinner', 'night_snack']
MEAL_QUALITIES = ['healthy', 'moderate', 'unhealthy']

# ============== Helper Functions ==============

def get_or_create_daily_log(user_id: int, log_date: date) -> int:
    """Get existing daily log or create new one. Returns log ID."""

    # Check if log exists
    results = execute_query(
        "SELECT id FROM daily_logs WHERE user_id = ? AND log_date = ?",
        (user_id, log_date.isoformat())
    )

    if results:
        return results[0]['id']

    # Create new log
    log_id = execute_insert(
        "INSERT INTO daily_logs (user_id, log_date) VALUES (?, ?)",
        (user_id, log_date.isoformat())
    )

    # Initialize default exercise entries
    for ex_type in EXERCISE_TYPES:
        execute_insert(
            "INSERT INTO exercise_entries (daily_log_id, exercise_type, completed) VALUES (?, ?, 0)",
            (log_id, ex_type)
        )

    # Initialize default meal entries
    for meal_type in MEAL_TYPES:
        execute_insert(
            "INSERT INTO meal_entries (daily_log_id, meal_type, completed) VALUES (?, ?, 0)",
            (log_id, meal_type)
        )

    # Initialize water entry
    execute_insert(
        "INSERT INTO water_entries (daily_log_id, glasses) VALUES (?, 0)",
        (log_id,)
    )

    return log_id


def get_exercises_for_log(log_id: int) -> list:
    """Get all exercise entries for a daily log."""
    results = execute_query(
        "SELECT * FROM exercise_entries WHERE daily_log_id = ? ORDER BY id",
        (log_id,)
    )
    return [ExerciseEntryResponse(
        id=r['id'],
        exercise_type=r['exercise_type'],
        completed=bool(r['completed']),
        duration_minutes=r['duration_minutes'],
        reps=r['reps'],
        notes=r['notes']
    ) for r in results]


def get_meals_for_log(log_id: int) -> list:
    """Get all meal entries for a daily log."""
    results = execute_query(
        "SELECT * FROM meal_entries WHERE daily_log_id = ? ORDER BY id",
        (log_id,)
    )
    return [MealEntryResponse(
        id=r['id'],
        meal_type=r['meal_type'],
        completed=bool(r['completed']),
        quality=r['quality'],
        portion_size=r['portion_size'],
        has_protein=bool(r['has_protein']),
        notes=r['notes']
    ) for r in results]


def get_water_for_log(log_id: int) -> int:
    """Get water glasses for a daily log."""
    results = execute_query(
        "SELECT glasses FROM water_entries WHERE daily_log_id = ?",
        (log_id,)
    )
    return results[0]['glasses'] if results else 0


def calculate_daily_score(exercises: list, meals: list, water_glasses: int) -> dict:
    """Calculate daily scores."""
    exercise_completed = sum(1 for e in exercises if e.completed)
    healthy_meals = sum(1 for m in meals if m.completed and m.quality == 'healthy')
    meals_completed = sum(1 for m in meals if m.completed)

    # Score calculation (out of 100):
    # - Exercises: 40 points (10 per exercise type)
    # - Meals: 40 points (10 per meal, bonus for healthy)
    # - Water: 20 points (2.5 per glass, max 8)

    exercise_score = exercise_completed * 10  # Max 40
    meal_score = meals_completed * 8 + healthy_meals * 2  # Max 40
    water_score = min(water_glasses * 2.5, 20)  # Max 20

    total_score = int(exercise_score + meal_score + water_score)

    return {
        'exercise_score': exercise_completed,
        'meal_score': healthy_meals,
        'total_score': min(total_score, 100)
    }


def log_to_response(log: dict) -> DailyLogResponse:
    """Convert database log to response model."""
    log_id = log['id']
    exercises = get_exercises_for_log(log_id)
    meals = get_meals_for_log(log_id)
    water_glasses = get_water_for_log(log_id)

    scores = calculate_daily_score(exercises, meals, water_glasses)

    return DailyLogResponse(
        id=log_id,
        user_id=log['user_id'],
        log_date=date.fromisoformat(log['log_date']),
        exercises=exercises,
        meals=meals,
        water_glasses=water_glasses,
        created_at=log.get('created_at'),
        updated_at=log.get('updated_at'),
        exercise_score=scores['exercise_score'],
        meal_score=scores['meal_score'],
        total_score=scores['total_score']
    )


def calculate_streak(user_id: int) -> dict:
    """Calculate current and best streak for user."""
    results = execute_query(
        """SELECT log_date FROM daily_logs
           WHERE user_id = ?
           ORDER BY log_date DESC""",
        (user_id,)
    )

    if not results:
        return {'current_streak': 0, 'best_streak': 0, 'last_logged_date': None}

    dates = [date.fromisoformat(r['log_date']) for r in results]
    today = date.today()

    # Calculate current streak
    current_streak = 0
    check_date = today

    for d in dates:
        if d == check_date or d == check_date - timedelta(days=1):
            current_streak += 1
            check_date = d - timedelta(days=1)
        else:
            break

    # Calculate best streak
    best_streak = 1
    temp_streak = 1

    for i in range(1, len(dates)):
        if dates[i-1] - dates[i] == timedelta(days=1):
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            temp_streak = 1

    return {
        'current_streak': current_streak,
        'best_streak': best_streak,
        'last_logged_date': dates[0] if dates else None
    }


# ============== API Endpoints ==============

@router.get("/today", response_model=DailyLogResponse)
async def get_today_log(current_user: dict = Depends(get_current_user)):
    """Get or create today's daily log."""
    user_id = current_user['id']
    today = date.today()

    log_id = get_or_create_daily_log(user_id, today)
    log = get_record_by_id('daily_logs', log_id)

    return log_to_response(log)


@router.get("/date/{log_date}", response_model=DailyLogResponse)
async def get_log_by_date(
    log_date: date,
    current_user: dict = Depends(get_current_user)
):
    """Get daily log for a specific date."""
    user_id = current_user['id']

    log_id = get_or_create_daily_log(user_id, log_date)
    log = get_record_by_id('daily_logs', log_id)

    return log_to_response(log)


@router.get("", response_model=DailyLogListResponse)
async def list_logs(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List daily logs with optional date range filter."""
    user_id = current_user['id']

    sql = "SELECT * FROM daily_logs WHERE user_id = ?"
    params = [user_id]

    if start_date:
        sql += " AND log_date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        sql += " AND log_date <= ?"
        params.append(end_date.isoformat())

    sql += " ORDER BY log_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    results = execute_query(sql, tuple(params))
    logs = [log_to_response(log) for log in results]

    # Get total count
    count_sql = "SELECT COUNT(*) as count FROM daily_logs WHERE user_id = ?"
    count_params = [user_id]
    if start_date:
        count_sql += " AND log_date >= ?"
        count_params.append(start_date.isoformat())
    if end_date:
        count_sql += " AND log_date <= ?"
        count_params.append(end_date.isoformat())

    total = execute_query(count_sql, tuple(count_params))[0]['count']

    return DailyLogListResponse(logs=logs, total=total)


@router.put("/date/{log_date}", response_model=DailyLogResponse)
async def update_daily_log(
    log_date: date,
    log_data: DailyLogCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update a daily log (create if doesn't exist)."""
    user_id = current_user['id']

    log_id = get_or_create_daily_log(user_id, log_date)

    # Update exercises
    for exercise in log_data.exercises:
        if exercise.exercise_type not in EXERCISE_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid exercise type: {exercise.exercise_type}")

        execute_update(
            """UPDATE exercise_entries
               SET completed = ?, duration_minutes = ?, reps = ?, notes = ?
               WHERE daily_log_id = ? AND exercise_type = ?""",
            (1 if exercise.completed else 0, exercise.duration_minutes,
             exercise.reps, exercise.notes, log_id, exercise.exercise_type)
        )

    # Update meals
    for meal in log_data.meals:
        if meal.meal_type not in MEAL_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid meal type: {meal.meal_type}")
        if meal.quality and meal.quality not in MEAL_QUALITIES:
            raise HTTPException(status_code=400, detail=f"Invalid meal quality: {meal.quality}")

        execute_update(
            """UPDATE meal_entries
               SET completed = ?, quality = ?, portion_size = ?, has_protein = ?, notes = ?
               WHERE daily_log_id = ? AND meal_type = ?""",
            (1 if meal.completed else 0, meal.quality, meal.portion_size,
             1 if meal.has_protein else 0, meal.notes, log_id, meal.meal_type)
        )

    # Update water
    execute_update(
        "UPDATE water_entries SET glasses = ? WHERE daily_log_id = ?",
        (log_data.water_glasses, log_id)
    )

    # Update timestamp
    execute_update(
        "UPDATE daily_logs SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), log_id)
    )

    log = get_record_by_id('daily_logs', log_id)
    return log_to_response(log)


@router.patch("/exercise/{log_date}/{exercise_type}")
async def toggle_exercise(
    log_date: date,
    exercise_type: str,
    completed: bool = Query(...),
    duration_minutes: Optional[int] = Query(None),
    reps: Optional[int] = Query(None),
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Quick toggle for a single exercise."""
    user_id = current_user['id']

    if exercise_type not in EXERCISE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid exercise type: {exercise_type}")

    log_id = get_or_create_daily_log(user_id, log_date)

    execute_update(
        """UPDATE exercise_entries
           SET completed = ?, duration_minutes = COALESCE(?, duration_minutes),
               reps = COALESCE(?, reps), notes = COALESCE(?, notes)
           WHERE daily_log_id = ? AND exercise_type = ?""",
        (1 if completed else 0, duration_minutes, reps, notes, log_id, exercise_type)
    )

    execute_update(
        "UPDATE daily_logs SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), log_id)
    )

    return {"status": "success", "exercise_type": exercise_type, "completed": completed}


@router.patch("/meal/{log_date}/{meal_type}")
async def toggle_meal(
    log_date: date,
    meal_type: str,
    completed: bool = Query(...),
    quality: Optional[str] = Query(None),
    portion_size: Optional[str] = Query(None),
    has_protein: Optional[bool] = Query(None),
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Quick toggle for a single meal."""
    user_id = current_user['id']

    if meal_type not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid meal type: {meal_type}")
    if quality and quality not in MEAL_QUALITIES:
        raise HTTPException(status_code=400, detail=f"Invalid meal quality: {quality}")

    log_id = get_or_create_daily_log(user_id, log_date)

    execute_update(
        """UPDATE meal_entries
           SET completed = ?, quality = COALESCE(?, quality),
               portion_size = COALESCE(?, portion_size),
               has_protein = COALESCE(?, has_protein),
               notes = COALESCE(?, notes)
           WHERE daily_log_id = ? AND meal_type = ?""",
        (1 if completed else 0, quality, portion_size,
         1 if has_protein else (0 if has_protein is not None else None),
         notes, log_id, meal_type)
    )

    execute_update(
        "UPDATE daily_logs SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), log_id)
    )

    return {"status": "success", "meal_type": meal_type, "completed": completed}


@router.patch("/water/{log_date}")
async def update_water(
    log_date: date,
    glasses: int = Query(..., ge=0, le=20),
    current_user: dict = Depends(get_current_user)
):
    """Update water intake for a day."""
    user_id = current_user['id']

    log_id = get_or_create_daily_log(user_id, log_date)

    execute_update(
        "UPDATE water_entries SET glasses = ? WHERE daily_log_id = ?",
        (glasses, log_id)
    )

    execute_update(
        "UPDATE daily_logs SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), log_id)
    )

    return {"status": "success", "glasses": glasses}


@router.get("/streak", response_model=StreakInfo)
async def get_streak(current_user: dict = Depends(get_current_user)):
    """Get current and best streak information."""
    user_id = current_user['id']
    streak_info = calculate_streak(user_id)
    return StreakInfo(**streak_info)


@router.get("/stats/weekly", response_model=WeeklyStats)
async def get_weekly_stats(
    week_offset: int = Query(0, description="0 = current week, -1 = last week, etc."),
    current_user: dict = Depends(get_current_user)
):
    """Get weekly statistics."""
    user_id = current_user['id']

    # Calculate week boundaries
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)

    # Get logs for the week
    logs = execute_query(
        """SELECT * FROM daily_logs
           WHERE user_id = ? AND log_date >= ? AND log_date <= ?""",
        (user_id, week_start.isoformat(), week_end.isoformat())
    )

    total_exercises = 0
    total_healthy_meals = 0
    total_water = 0
    total_score = 0

    for log in logs:
        exercises = get_exercises_for_log(log['id'])
        meals = get_meals_for_log(log['id'])
        water = get_water_for_log(log['id'])

        total_exercises += sum(1 for e in exercises if e.completed)
        total_healthy_meals += sum(1 for m in meals if m.completed and m.quality == 'healthy')
        total_water += water

        scores = calculate_daily_score(exercises, meals, water)
        total_score += scores['total_score']

    days_logged = len(logs)
    streak_info = calculate_streak(user_id)

    return WeeklyStats(
        week_start=week_start,
        week_end=week_end,
        days_logged=days_logged,
        total_exercises_completed=total_exercises,
        total_healthy_meals=total_healthy_meals,
        average_water_glasses=round(total_water / max(days_logged, 1), 1),
        average_daily_score=round(total_score / max(days_logged, 1), 1),
        current_streak=streak_info['current_streak'],
        best_streak=streak_info['best_streak']
    )


@router.get("/stats/monthly", response_model=MonthlyStats)
async def get_monthly_stats(
    month_offset: int = Query(0, description="0 = current month, -1 = last month, etc."),
    current_user: dict = Depends(get_current_user)
):
    """Get monthly statistics."""
    user_id = current_user['id']

    # Calculate month boundaries
    today = date.today()
    first_of_month = date(today.year, today.month, 1)

    # Apply offset
    for _ in range(abs(month_offset)):
        if month_offset < 0:
            first_of_month = (first_of_month - timedelta(days=1)).replace(day=1)
        else:
            next_month = first_of_month.replace(day=28) + timedelta(days=4)
            first_of_month = next_month.replace(day=1)

    # Get last day of month
    if first_of_month.month == 12:
        last_of_month = date(first_of_month.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_of_month = date(first_of_month.year, first_of_month.month + 1, 1) - timedelta(days=1)

    # Get logs for the month
    logs = execute_query(
        """SELECT * FROM daily_logs
           WHERE user_id = ? AND log_date >= ? AND log_date <= ?""",
        (user_id, first_of_month.isoformat(), last_of_month.isoformat())
    )

    total_exercises = 0
    total_healthy_meals = 0
    total_water = 0
    total_score = 0
    exercise_breakdown = {ex: 0 for ex in EXERCISE_TYPES}
    meal_quality_breakdown = {'healthy': 0, 'moderate': 0, 'unhealthy': 0}

    for log in logs:
        exercises = get_exercises_for_log(log['id'])
        meals = get_meals_for_log(log['id'])
        water = get_water_for_log(log['id'])

        for e in exercises:
            if e.completed:
                total_exercises += 1
                exercise_breakdown[e.exercise_type] += 1

        for m in meals:
            if m.completed:
                if m.quality == 'healthy':
                    total_healthy_meals += 1
                    meal_quality_breakdown['healthy'] += 1
                elif m.quality == 'moderate':
                    meal_quality_breakdown['moderate'] += 1
                elif m.quality == 'unhealthy':
                    meal_quality_breakdown['unhealthy'] += 1

        total_water += water
        scores = calculate_daily_score(exercises, meals, water)
        total_score += scores['total_score']

    days_logged = len(logs)

    return MonthlyStats(
        month=first_of_month.strftime("%Y-%m"),
        days_logged=days_logged,
        total_exercises_completed=total_exercises,
        total_healthy_meals=total_healthy_meals,
        average_water_glasses=round(total_water / max(days_logged, 1), 1),
        average_daily_score=round(total_score / max(days_logged, 1), 1),
        exercise_breakdown=exercise_breakdown,
        meal_quality_breakdown=meal_quality_breakdown
    )
```

### File: `api/main.py` (MODIFY - Add router)

Add this import and include the router:

```python
# Add this import at the top
from api.routers.habits import router as habits_router

# Add this line after the other router includes (around line 38)
app.include_router(habits_router)
```

---

## Part 3: Frontend Implementation

### File: `frontend/src/types/habits.ts` (NEW FILE)

```typescript
// Exercise types
export type ExerciseType = 'hip_exercises' | 'upper_body' | 'walk' | 'yoga' | 'eye_exercises' | 'meditation' | 'cardio';

export interface ExerciseEntry {
    id?: number;
    exercise_type: ExerciseType;
    completed: boolean;
    duration_minutes?: number | null;
    reps?: number | null;
    notes?: string | null;
}

// Meal types
export type MealType = 'breakfast' | 'lunch' | 'evening_snack' | 'dinner' | 'night_snack';
export type MealQuality = 'healthy' | 'moderate' | 'unhealthy';
export type PortionSize = 'small' | 'medium' | 'large';

export interface MealEntry {
    id?: number;
    meal_type: MealType;
    completed: boolean;
    quality?: MealQuality | null;
    portion_size?: PortionSize | null;
    has_protein?: boolean;
    notes?: string | null;  // what specifically you ate
}

// Daily log
export interface DailyLog {
    id: number;
    user_id: number;
    log_date: string;  // ISO date string
    exercises: ExerciseEntry[];
    meals: MealEntry[];
    water_glasses: number;
    created_at?: string;
    updated_at?: string;
    exercise_score: number;
    meal_score: number;
    total_score: number;
}

export interface DailyLogCreate {
    log_date: string;
    exercises: ExerciseEntry[];
    meals: MealEntry[];
    water_glasses: number;
}

export interface DailyLogListResponse {
    logs: DailyLog[];
    total: number;
}

// Stats
export interface StreakInfo {
    current_streak: number;
    best_streak: number;
    last_logged_date?: string | null;
}

export interface WeeklyStats {
    week_start: string;
    week_end: string;
    days_logged: number;
    total_exercises_completed: number;
    total_healthy_meals: number;
    average_water_glasses: number;
    average_daily_score: number;
    current_streak: number;
    best_streak: number;
}

export interface MonthlyStats {
    month: string;
    days_logged: number;
    total_exercises_completed: number;
    total_healthy_meals: number;
    average_water_glasses: number;
    average_daily_score: number;
    exercise_breakdown: Record<ExerciseType, number>;
    meal_quality_breakdown: Record<MealQuality, number>;
}

// Filter for listing logs
export interface HabitsFilter {
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
}

// Constants for display
export const EXERCISE_LABELS: Record<ExerciseType, string> = {
    hip_exercises: 'Hip Exercises',
    upper_body: 'Upper Body',
    walk: 'Walk',
    yoga: 'Yoga',
    eye_exercises: 'Eye Exercises',
    meditation: 'Meditation',
    cardio: 'Cardio'
};

export const EXERCISE_ICONS: Record<ExerciseType, string> = {
    hip_exercises: '🦵',
    upper_body: '💪',
    walk: '🚶',
    yoga: '🧘',
    eye_exercises: '👁️',
    meditation: '🧘‍♂️',
    cardio: '🏃'
};

export const MEAL_LABELS: Record<MealType, string> = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    evening_snack: 'Evening Snack',
    dinner: 'Dinner',
    night_snack: 'Night Snack'
};

export const MEAL_ICONS: Record<MealType, string> = {
    breakfast: '🍳',
    lunch: '🍛',
    evening_snack: '🥜',
    dinner: '🍚',
    night_snack: '🍪'
};

export const QUALITY_COLORS: Record<MealQuality, string> = {
    healthy: 'text-green-400 bg-green-400/10',
    moderate: 'text-yellow-400 bg-yellow-400/10',
    unhealthy: 'text-red-400 bg-red-400/10'
};

export const PORTION_LABELS: Record<PortionSize, string> = {
    small: 'Small',
    medium: 'Medium',
    large: 'Large'
};
```

### File: `frontend/src/api/habits.ts` (NEW FILE)

```typescript
import api from './client';
import type {
    DailyLog,
    DailyLogCreate,
    DailyLogListResponse,
    StreakInfo,
    WeeklyStats,
    MonthlyStats,
    HabitsFilter,
    ExerciseType,
    MealType,
    MealQuality,
    PortionSize
} from '../types/habits';

export const habitsApi = {
    // Get today's log
    async getToday(): Promise<DailyLog> {
        const response = await api.get<DailyLog>('/api/habits/today');
        return response.data;
    },

    // Get log by date
    async getByDate(date: string): Promise<DailyLog> {
        const response = await api.get<DailyLog>(`/api/habits/date/${date}`);
        return response.data;
    },

    // List logs with filters
    async list(filters: HabitsFilter = {}): Promise<DailyLogListResponse> {
        const params = new URLSearchParams();
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.limit) params.append('limit', filters.limit.toString());
        if (filters.offset) params.append('offset', filters.offset.toString());

        const response = await api.get<DailyLogListResponse>(`/api/habits?${params.toString()}`);
        return response.data;
    },

    // Update full daily log
    async updateLog(date: string, data: DailyLogCreate): Promise<DailyLog> {
        const response = await api.put<DailyLog>(`/api/habits/date/${date}`, data);
        return response.data;
    },

    // Quick toggle exercise
    async toggleExercise(
        date: string,
        exerciseType: ExerciseType,
        completed: boolean,
        durationMinutes?: number,
        reps?: number,
        notes?: string
    ): Promise<void> {
        const params = new URLSearchParams();
        params.append('completed', completed.toString());
        if (durationMinutes !== undefined) params.append('duration_minutes', durationMinutes.toString());
        if (reps !== undefined) params.append('reps', reps.toString());
        if (notes) params.append('notes', notes);

        await api.patch(`/api/habits/exercise/${date}/${exerciseType}?${params.toString()}`);
    },

    // Quick toggle meal
    async toggleMeal(
        date: string,
        mealType: MealType,
        completed: boolean,
        quality?: MealQuality,
        portionSize?: PortionSize,
        hasProtein?: boolean,
        notes?: string
    ): Promise<void> {
        const params = new URLSearchParams();
        params.append('completed', completed.toString());
        if (quality) params.append('quality', quality);
        if (portionSize) params.append('portion_size', portionSize);
        if (hasProtein !== undefined) params.append('has_protein', hasProtein.toString());
        if (notes) params.append('notes', notes);

        await api.patch(`/api/habits/meal/${date}/${mealType}?${params.toString()}`);
    },

    // Update water intake
    async updateWater(date: string, glasses: number): Promise<void> {
        await api.patch(`/api/habits/water/${date}?glasses=${glasses}`);
    },

    // Get streak info
    async getStreak(): Promise<StreakInfo> {
        const response = await api.get<StreakInfo>('/api/habits/streak');
        return response.data;
    },

    // Get weekly stats
    async getWeeklyStats(weekOffset: number = 0): Promise<WeeklyStats> {
        const response = await api.get<WeeklyStats>(`/api/habits/stats/weekly?week_offset=${weekOffset}`);
        return response.data;
    },

    // Get monthly stats
    async getMonthlyStats(monthOffset: number = 0): Promise<MonthlyStats> {
        const response = await api.get<MonthlyStats>(`/api/habits/stats/monthly?month_offset=${monthOffset}`);
        return response.data;
    }
};
```

### File: `frontend/src/hooks/useHabits.ts` (NEW FILE)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { habitsApi } from '../api/habits';
import type { DailyLogCreate, HabitsFilter, ExerciseType, MealType, MealQuality } from '../types/habits';

// Query keys
export const habitsKeys = {
    all: ['habits'] as const,
    today: () => [...habitsKeys.all, 'today'] as const,
    date: (date: string) => [...habitsKeys.all, 'date', date] as const,
    list: (filters: HabitsFilter) => [...habitsKeys.all, 'list', filters] as const,
    streak: () => [...habitsKeys.all, 'streak'] as const,
    weeklyStats: (offset: number) => [...habitsKeys.all, 'weekly', offset] as const,
    monthlyStats: (offset: number) => [...habitsKeys.all, 'monthly', offset] as const,
};

// Get today's log
export function useTodayLog() {
    return useQuery({
        queryKey: habitsKeys.today(),
        queryFn: () => habitsApi.getToday(),
    });
}

// Get log by date
export function useLogByDate(date: string) {
    return useQuery({
        queryKey: habitsKeys.date(date),
        queryFn: () => habitsApi.getByDate(date),
        enabled: !!date,
    });
}

// List logs
export function useHabitsLogs(filters: HabitsFilter = {}) {
    return useQuery({
        queryKey: habitsKeys.list(filters),
        queryFn: () => habitsApi.list(filters),
    });
}

// Get streak
export function useStreak() {
    return useQuery({
        queryKey: habitsKeys.streak(),
        queryFn: () => habitsApi.getStreak(),
    });
}

// Get weekly stats
export function useWeeklyStats(weekOffset: number = 0) {
    return useQuery({
        queryKey: habitsKeys.weeklyStats(weekOffset),
        queryFn: () => habitsApi.getWeeklyStats(weekOffset),
    });
}

// Get monthly stats
export function useMonthlyStats(monthOffset: number = 0) {
    return useQuery({
        queryKey: habitsKeys.monthlyStats(monthOffset),
        queryFn: () => habitsApi.getMonthlyStats(monthOffset),
    });
}

// Toggle exercise mutation
export function useToggleExercise() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            date,
            exerciseType,
            completed,
            durationMinutes,
            reps,
            notes
        }: {
            date: string;
            exerciseType: ExerciseType;
            completed: boolean;
            durationMinutes?: number;
            reps?: number;
            notes?: string;
        }) => habitsApi.toggleExercise(date, exerciseType, completed, durationMinutes, reps, notes),
        onSuccess: (_, { date }) => {
            queryClient.invalidateQueries({ queryKey: habitsKeys.today() });
            queryClient.invalidateQueries({ queryKey: habitsKeys.date(date) });
            queryClient.invalidateQueries({ queryKey: habitsKeys.streak() });
        },
    });
}

// Toggle meal mutation
export function useToggleMeal() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            date,
            mealType,
            completed,
            quality,
            portionSize,
            hasProtein,
            notes
        }: {
            date: string;
            mealType: MealType;
            completed: boolean;
            quality?: MealQuality;
            portionSize?: PortionSize;
            hasProtein?: boolean;
            notes?: string;
        }) => habitsApi.toggleMeal(date, mealType, completed, quality, portionSize, hasProtein, notes),
        onSuccess: (_, { date }) => {
            queryClient.invalidateQueries({ queryKey: habitsKeys.today() });
            queryClient.invalidateQueries({ queryKey: habitsKeys.date(date) });
            queryClient.invalidateQueries({ queryKey: habitsKeys.streak() });
        },
    });
}

// Update water mutation
export function useUpdateWater() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ date, glasses }: { date: string; glasses: number }) =>
            habitsApi.updateWater(date, glasses),
        onSuccess: (_, { date }) => {
            queryClient.invalidateQueries({ queryKey: habitsKeys.today() });
            queryClient.invalidateQueries({ queryKey: habitsKeys.date(date) });
        },
    });
}

// Update full log mutation
export function useUpdateLog() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ date, data }: { date: string; data: DailyLogCreate }) =>
            habitsApi.updateLog(date, data),
        onSuccess: (_, { date }) => {
            queryClient.invalidateQueries({ queryKey: habitsKeys.today() });
            queryClient.invalidateQueries({ queryKey: habitsKeys.date(date) });
            queryClient.invalidateQueries({ queryKey: habitsKeys.streak() });
            queryClient.invalidateQueries({ queryKey: habitsKeys.list({}) });
        },
    });
}
```

### File: `frontend/src/components/habits/DailyTracker.tsx` (NEW FILE)

```tsx
import { useState } from 'react';
import { format } from 'date-fns';
import {
    useTodayLog,
    useLogByDate,
    useToggleExercise,
    useToggleMeal,
    useUpdateWater,
    useStreak
} from '../../hooks/useHabits';
import {
    EXERCISE_LABELS,
    EXERCISE_ICONS,
    MEAL_LABELS,
    MEAL_ICONS,
    QUALITY_COLORS,
    PORTION_LABELS,
    type ExerciseType,
    type MealType,
    type MealQuality,
    type PortionSize
} from '../../types/habits';
import HabitsReports from './HabitsReports';

interface DailyTrackerProps {
    initialDate?: string;
}

export default function DailyTracker({ initialDate }: DailyTrackerProps) {
    const [selectedDate, setSelectedDate] = useState(initialDate || format(new Date(), 'yyyy-MM-dd'));
    const [activeTab, setActiveTab] = useState<'today' | 'reports'>('today');
    const [expandedExercise, setExpandedExercise] = useState<ExerciseType | null>(null);
    const [expandedMeal, setExpandedMeal] = useState<MealType | null>(null);

    const isToday = selectedDate === format(new Date(), 'yyyy-MM-dd');

    const { data: log, isLoading } = isToday
        ? useTodayLog()
        : useLogByDate(selectedDate);

    const { data: streak } = useStreak();

    const toggleExercise = useToggleExercise();
    const toggleMeal = useToggleMeal();
    const updateWater = useUpdateWater();

    const handleExerciseToggle = (exerciseType: ExerciseType, currentCompleted: boolean) => {
        toggleExercise.mutate({
            date: selectedDate,
            exerciseType,
            completed: !currentCompleted
        });
    };

    const handleExerciseUpdate = (exerciseType: ExerciseType, duration?: number, reps?: number, notes?: string) => {
        const exercise = log?.exercises.find(e => e.exercise_type === exerciseType);
        toggleExercise.mutate({
            date: selectedDate,
            exerciseType,
            completed: exercise?.completed || false,
            durationMinutes: duration,
            reps,
            notes
        });
        setExpandedExercise(null);
    };

    const handleMealToggle = (mealType: MealType, currentCompleted: boolean, quality?: MealQuality) => {
        toggleMeal.mutate({
            date: selectedDate,
            mealType,
            completed: !currentCompleted,
            quality: quality || 'moderate'
        });
    };

    const handleMealUpdate = (mealType: MealType, quality: MealQuality, portionSize?: PortionSize, hasProtein?: boolean, notes?: string) => {
        const meal = log?.meals.find(m => m.meal_type === mealType);
        toggleMeal.mutate({
            date: selectedDate,
            mealType,
            completed: meal?.completed || true,
            quality,
            portionSize,
            hasProtein,
            notes
        });
        setExpandedMeal(null);
    };

    const handleWaterChange = (delta: number) => {
        const currentGlasses = log?.water_glasses || 0;
        const newGlasses = Math.max(0, Math.min(20, currentGlasses + delta));
        updateWater.mutate({ date: selectedDate, glasses: newGlasses });
    };

    if (isLoading) {
        return (
            <div className="flex-1 bg-[#1e1e1e] flex items-center justify-center">
                <div className="text-gray-500">Loading...</div>
            </div>
        );
    }

    return (
        <div className="flex-1 bg-[#1e1e1e] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="bg-[#252525] border-b border-gray-800 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-semibold text-white">Daily Tracker</h1>

                        {/* Streak Badge */}
                        {streak && streak.current_streak > 0 && (
                            <div className="flex items-center gap-1 px-3 py-1 bg-orange-500/20 rounded-full">
                                <span className="text-orange-400">🔥</span>
                                <span className="text-orange-400 text-sm font-medium">
                                    {streak.current_streak} day streak
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Tab Buttons */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setActiveTab('today')}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                                activeTab === 'today'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-[#333] text-gray-400 hover:text-white'
                            }`}
                        >
                            Today
                        </button>
                        <button
                            onClick={() => setActiveTab('reports')}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                                activeTab === 'reports'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-[#333] text-gray-400 hover:text-white'
                            }`}
                        >
                            Reports
                        </button>
                    </div>
                </div>

                {/* Date Picker - Only show in Today tab */}
                {activeTab === 'today' && (
                    <div className="flex items-center gap-3 mt-4">
                        <button
                            onClick={() => {
                                const d = new Date(selectedDate);
                                d.setDate(d.getDate() - 1);
                                setSelectedDate(format(d, 'yyyy-MM-dd'));
                            }}
                            className="p-2 hover:bg-[#333] rounded-lg transition-colors text-gray-400"
                        >
                            ←
                        </button>
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="bg-[#333] text-white px-4 py-2 rounded-lg border border-gray-700 text-sm"
                        />
                        <button
                            onClick={() => {
                                const d = new Date(selectedDate);
                                d.setDate(d.getDate() + 1);
                                setSelectedDate(format(d, 'yyyy-MM-dd'));
                            }}
                            className="p-2 hover:bg-[#333] rounded-lg transition-colors text-gray-400"
                        >
                            →
                        </button>
                        {!isToday && (
                            <button
                                onClick={() => setSelectedDate(format(new Date(), 'yyyy-MM-dd'))}
                                className="px-3 py-2 text-sm text-blue-400 hover:text-blue-300"
                            >
                                Go to Today
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                {activeTab === 'today' ? (
                    <div className="max-w-2xl mx-auto space-y-6">
                        {/* Score Summary */}
                        {log && (
                            <div className="bg-[#252525] rounded-xl p-4 border border-gray-800">
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-400 text-sm">Daily Score</span>
                                    <span className={`text-2xl font-bold ${
                                        log.total_score >= 80 ? 'text-green-400' :
                                        log.total_score >= 50 ? 'text-yellow-400' :
                                        'text-red-400'
                                    }`}>
                                        {log.total_score}/100
                                    </span>
                                </div>
                                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${
                                            log.total_score >= 80 ? 'bg-green-500' :
                                            log.total_score >= 50 ? 'bg-yellow-500' :
                                            'bg-red-500'
                                        }`}
                                        style={{ width: `${log.total_score}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Exercise Section */}
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800">
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                🏋️ Exercise
                            </h2>
                            <div className="space-y-3">
                                {(['hip_exercises', 'upper_body', 'walk', 'yoga', 'eye_exercises', 'meditation', 'cardio'] as ExerciseType[]).map((type) => {
                                    const exercise = log?.exercises.find(e => e.exercise_type === type);
                                    const isExpanded = expandedExercise === type;

                                    return (
                                        <div key={type} className="bg-[#1e1e1e] rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={() => handleExerciseToggle(type, exercise?.completed || false)}
                                                        className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                                                            exercise?.completed
                                                                ? 'bg-green-500 border-green-500 text-white'
                                                                : 'border-gray-600 hover:border-gray-500'
                                                        }`}
                                                    >
                                                        {exercise?.completed && '✓'}
                                                    </button>
                                                    <span className="text-lg">{EXERCISE_ICONS[type]}</span>
                                                    <span className="text-white">{EXERCISE_LABELS[type]}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {exercise?.duration_minutes && (
                                                        <span className="text-sm text-gray-400">
                                                            {exercise.duration_minutes} min
                                                        </span>
                                                    )}
                                                    {exercise?.reps && (
                                                        <span className="text-sm text-gray-400">
                                                            {exercise.reps} reps
                                                        </span>
                                                    )}
                                                    <button
                                                        onClick={() => setExpandedExercise(isExpanded ? null : type)}
                                                        className="p-1 hover:bg-[#333] rounded text-gray-400"
                                                    >
                                                        {isExpanded ? '▲' : '▼'}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Expanded Details */}
                                            {isExpanded && (
                                                <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
                                                    <div className="flex items-center gap-4">
                                                        <div className="flex items-center gap-2">
                                                            <label className="text-sm text-gray-400">Duration:</label>
                                                            <input
                                                                type="number"
                                                                placeholder="min"
                                                                defaultValue={exercise?.duration_minutes || ''}
                                                                className="bg-[#333] text-white px-3 py-1.5 rounded text-sm w-20 border border-gray-700"
                                                                onBlur={(e) => {
                                                                    const val = parseInt(e.target.value);
                                                                    handleExerciseUpdate(type, !isNaN(val) ? val : undefined, exercise?.reps || undefined, exercise?.notes || undefined);
                                                                }}
                                                            />
                                                            <span className="text-sm text-gray-500">min</span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <label className="text-sm text-gray-400">Reps:</label>
                                                            <input
                                                                type="number"
                                                                placeholder="reps"
                                                                defaultValue={exercise?.reps || ''}
                                                                className="bg-[#333] text-white px-3 py-1.5 rounded text-sm w-20 border border-gray-700"
                                                                onBlur={(e) => {
                                                                    const val = parseInt(e.target.value);
                                                                    handleExerciseUpdate(type, exercise?.duration_minutes || undefined, !isNaN(val) ? val : undefined, exercise?.notes || undefined);
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="text-sm text-gray-400 block mb-1">Notes:</label>
                                                        <input
                                                            type="text"
                                                            placeholder="Optional notes..."
                                                            defaultValue={exercise?.notes || ''}
                                                            className="w-full bg-[#333] text-white px-3 py-1.5 rounded text-sm border border-gray-700"
                                                            onBlur={(e) => {
                                                                handleExerciseUpdate(type, exercise?.duration_minutes || undefined, exercise?.reps || undefined, e.target.value || undefined);
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Meals Section */}
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800">
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                🍽️ Meals
                            </h2>
                            <div className="space-y-3">
                                {(['breakfast', 'lunch', 'evening_snack', 'dinner', 'night_snack'] as MealType[]).map((type) => {
                                    const meal = log?.meals.find(m => m.meal_type === type);
                                    const isExpanded = expandedMeal === type;

                                    return (
                                        <div key={type} className="bg-[#1e1e1e] rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={() => handleMealToggle(type, meal?.completed || false, meal?.quality as MealQuality)}
                                                        className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                                                            meal?.completed
                                                                ? 'bg-green-500 border-green-500 text-white'
                                                                : 'border-gray-600 hover:border-gray-500'
                                                        }`}
                                                    >
                                                        {meal?.completed && '✓'}
                                                    </button>
                                                    <span className="text-lg">{MEAL_ICONS[type]}</span>
                                                    <span className="text-white">{MEAL_LABELS[type]}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {meal?.has_protein && meal.completed && (
                                                        <span className="text-xs px-2 py-0.5 rounded bg-purple-400/10 text-purple-400">
                                                            🥩 Protein
                                                        </span>
                                                    )}
                                                    {meal?.portion_size && meal.completed && (
                                                        <span className="text-xs px-2 py-0.5 rounded bg-gray-600 text-gray-300">
                                                            {PORTION_LABELS[meal.portion_size as PortionSize]}
                                                        </span>
                                                    )}
                                                    {meal?.quality && meal.completed && (
                                                        <span className={`text-xs px-2 py-0.5 rounded ${QUALITY_COLORS[meal.quality]}`}>
                                                            {meal.quality}
                                                        </span>
                                                    )}
                                                    <button
                                                        onClick={() => setExpandedMeal(isExpanded ? null : type)}
                                                        className="p-1 hover:bg-[#333] rounded text-gray-400"
                                                    >
                                                        {isExpanded ? '▲' : '▼'}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Expanded Details */}
                                            {isExpanded && (
                                                <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
                                                    <div>
                                                        <label className="text-sm text-gray-400 block mb-2">Quality:</label>
                                                        <div className="flex gap-2">
                                                            {(['healthy', 'moderate', 'unhealthy'] as MealQuality[]).map((q) => (
                                                                <button
                                                                    key={q}
                                                                    onClick={() => handleMealUpdate(type, q, meal?.portion_size as PortionSize, meal?.has_protein, meal?.notes || undefined)}
                                                                    className={`px-3 py-1.5 rounded text-sm capitalize transition-colors ${
                                                                        meal?.quality === q
                                                                            ? QUALITY_COLORS[q]
                                                                            : 'bg-[#333] text-gray-400 hover:text-white'
                                                                    }`}
                                                                >
                                                                    {q}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="text-sm text-gray-400 block mb-2">Portion Size:</label>
                                                        <div className="flex gap-2">
                                                            {(['small', 'medium', 'large'] as PortionSize[]).map((size) => (
                                                                <button
                                                                    key={size}
                                                                    onClick={() => handleMealUpdate(type, meal?.quality as MealQuality || 'moderate', size, meal?.has_protein, meal?.notes || undefined)}
                                                                    className={`px-3 py-1.5 rounded text-sm capitalize transition-colors ${
                                                                        meal?.portion_size === size
                                                                            ? 'bg-blue-500/20 text-blue-400'
                                                                            : 'bg-[#333] text-gray-400 hover:text-white'
                                                                    }`}
                                                                >
                                                                    {PORTION_LABELS[size]}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <label className="text-sm text-gray-400">Has Protein:</label>
                                                        <button
                                                            onClick={() => handleMealUpdate(type, meal?.quality as MealQuality || 'moderate', meal?.portion_size as PortionSize, !meal?.has_protein, meal?.notes || undefined)}
                                                            className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                                                                meal?.has_protein
                                                                    ? 'bg-purple-500 border-purple-500 text-white'
                                                                    : 'border-gray-600 hover:border-gray-500'
                                                            }`}
                                                        >
                                                            {meal?.has_protein && '✓'}
                                                        </button>
                                                        <span className="text-xs text-gray-500">Did meal have adequate protein?</span>
                                                    </div>
                                                    <div>
                                                        <label className="text-sm text-gray-400 block mb-1">What did you eat?</label>
                                                        <input
                                                            type="text"
                                                            placeholder="e.g., Oatmeal with fruits, eggs..."
                                                            defaultValue={meal?.notes || ''}
                                                            className="w-full bg-[#333] text-white px-3 py-1.5 rounded text-sm border border-gray-700"
                                                            onBlur={(e) => {
                                                                handleMealUpdate(type, meal?.quality as MealQuality || 'moderate', meal?.portion_size as PortionSize, meal?.has_protein, e.target.value || undefined);
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Water Section */}
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800">
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                💧 Water Intake
                            </h2>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => handleWaterChange(-1)}
                                        className="w-10 h-10 bg-[#333] hover:bg-[#444] rounded-lg text-white text-xl transition-colors"
                                    >
                                        -
                                    </button>
                                    <div className="text-center">
                                        <span className="text-3xl font-bold text-blue-400">
                                            {log?.water_glasses || 0}
                                        </span>
                                        <span className="text-gray-400 text-lg"> / 8</span>
                                        <p className="text-xs text-gray-500 mt-1">glasses</p>
                                    </div>
                                    <button
                                        onClick={() => handleWaterChange(1)}
                                        className="w-10 h-10 bg-[#333] hover:bg-[#444] rounded-lg text-white text-xl transition-colors"
                                    >
                                        +
                                    </button>
                                </div>

                                {/* Visual glasses */}
                                <div className="flex gap-1">
                                    {Array.from({ length: 8 }).map((_, i) => (
                                        <div
                                            key={i}
                                            className={`w-4 h-8 rounded-sm transition-colors ${
                                                i < (log?.water_glasses || 0)
                                                    ? 'bg-blue-500'
                                                    : 'bg-gray-700'
                                            }`}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <HabitsReports />
                )}
            </div>
        </div>
    );
}
```

### File: `frontend/src/components/habits/HabitsReports.tsx` (NEW FILE)

```tsx
import { useState } from 'react';
import { format } from 'date-fns';
import { useWeeklyStats, useMonthlyStats, useStreak, useHabitsLogs } from '../../hooks/useHabits';
import { EXERCISE_LABELS, EXERCISE_ICONS } from '../../types/habits';

export default function HabitsReports() {
    const [weekOffset, setWeekOffset] = useState(0);
    const [monthOffset, setMonthOffset] = useState(0);

    const { data: streak } = useStreak();
    const { data: weeklyStats, isLoading: weeklyLoading } = useWeeklyStats(weekOffset);
    const { data: monthlyStats, isLoading: monthlyLoading } = useMonthlyStats(monthOffset);

    // Get recent logs for history
    const { data: recentLogs } = useHabitsLogs({ limit: 7 });

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Streak Cards */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/10 rounded-xl p-5 border border-orange-500/30">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">🔥</span>
                        <span className="text-orange-400 text-sm font-medium">Current Streak</span>
                    </div>
                    <p className="text-4xl font-bold text-white">
                        {streak?.current_streak || 0}
                        <span className="text-lg text-gray-400 ml-2">days</span>
                    </p>
                </div>

                <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 rounded-xl p-5 border border-purple-500/30">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">🏆</span>
                        <span className="text-purple-400 text-sm font-medium">Best Streak</span>
                    </div>
                    <p className="text-4xl font-bold text-white">
                        {streak?.best_streak || 0}
                        <span className="text-lg text-gray-400 ml-2">days</span>
                    </p>
                </div>
            </div>

            {/* Weekly Stats */}
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white">Weekly Summary</h2>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setWeekOffset(weekOffset - 1)}
                            className="px-3 py-1 bg-[#333] hover:bg-[#444] rounded text-sm text-gray-400"
                        >
                            ← Prev
                        </button>
                        <span className="text-sm text-gray-400 min-w-[140px] text-center">
                            {weeklyStats && `${format(new Date(weeklyStats.week_start), 'MMM d')} - ${format(new Date(weeklyStats.week_end), 'MMM d')}`}
                        </span>
                        <button
                            onClick={() => setWeekOffset(Math.min(0, weekOffset + 1))}
                            disabled={weekOffset >= 0}
                            className="px-3 py-1 bg-[#333] hover:bg-[#444] rounded text-sm text-gray-400 disabled:opacity-50"
                        >
                            Next →
                        </button>
                    </div>
                </div>

                {weeklyLoading ? (
                    <div className="text-gray-500 text-center py-8">Loading...</div>
                ) : weeklyStats && (
                    <div className="grid grid-cols-4 gap-4">
                        <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                            <p className="text-gray-400 text-xs mb-1">Days Logged</p>
                            <p className="text-2xl font-bold text-white">{weeklyStats.days_logged}/7</p>
                        </div>
                        <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                            <p className="text-gray-400 text-xs mb-1">Exercises Done</p>
                            <p className="text-2xl font-bold text-green-400">{weeklyStats.total_exercises_completed}</p>
                        </div>
                        <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                            <p className="text-gray-400 text-xs mb-1">Healthy Meals</p>
                            <p className="text-2xl font-bold text-blue-400">{weeklyStats.total_healthy_meals}</p>
                        </div>
                        <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                            <p className="text-gray-400 text-xs mb-1">Avg Score</p>
                            <p className={`text-2xl font-bold ${
                                weeklyStats.average_daily_score >= 80 ? 'text-green-400' :
                                weeklyStats.average_daily_score >= 50 ? 'text-yellow-400' :
                                'text-red-400'
                            }`}>{weeklyStats.average_daily_score}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Monthly Stats */}
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white">Monthly Summary</h2>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setMonthOffset(monthOffset - 1)}
                            className="px-3 py-1 bg-[#333] hover:bg-[#444] rounded text-sm text-gray-400"
                        >
                            ← Prev
                        </button>
                        <span className="text-sm text-gray-400 min-w-[100px] text-center">
                            {monthlyStats && format(new Date(monthlyStats.month + '-01'), 'MMMM yyyy')}
                        </span>
                        <button
                            onClick={() => setMonthOffset(Math.min(0, monthOffset + 1))}
                            disabled={monthOffset >= 0}
                            className="px-3 py-1 bg-[#333] hover:bg-[#444] rounded text-sm text-gray-400 disabled:opacity-50"
                        >
                            Next →
                        </button>
                    </div>
                </div>

                {monthlyLoading ? (
                    <div className="text-gray-500 text-center py-8">Loading...</div>
                ) : monthlyStats && (
                    <div className="space-y-4">
                        {/* Stats Row */}
                        <div className="grid grid-cols-4 gap-4">
                            <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                                <p className="text-gray-400 text-xs mb-1">Days Logged</p>
                                <p className="text-2xl font-bold text-white">{monthlyStats.days_logged}</p>
                            </div>
                            <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                                <p className="text-gray-400 text-xs mb-1">Exercises</p>
                                <p className="text-2xl font-bold text-green-400">{monthlyStats.total_exercises_completed}</p>
                            </div>
                            <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                                <p className="text-gray-400 text-xs mb-1">Healthy Meals</p>
                                <p className="text-2xl font-bold text-blue-400">{monthlyStats.total_healthy_meals}</p>
                            </div>
                            <div className="bg-[#1e1e1e] rounded-lg p-4 text-center">
                                <p className="text-gray-400 text-xs mb-1">Avg Water</p>
                                <p className="text-2xl font-bold text-cyan-400">{monthlyStats.average_water_glasses}</p>
                            </div>
                        </div>

                        {/* Exercise Breakdown */}
                        <div className="bg-[#1e1e1e] rounded-lg p-4">
                            <p className="text-gray-400 text-xs mb-3">Exercise Breakdown</p>
                            <div className="flex gap-6">
                                {Object.entries(monthlyStats.exercise_breakdown).map(([type, count]) => (
                                    <div key={type} className="flex items-center gap-2">
                                        <span>{EXERCISE_ICONS[type as keyof typeof EXERCISE_ICONS]}</span>
                                        <span className="text-white">{count}</span>
                                        <span className="text-gray-500 text-sm">{EXERCISE_LABELS[type as keyof typeof EXERCISE_LABELS]}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Meal Quality Breakdown */}
                        <div className="bg-[#1e1e1e] rounded-lg p-4">
                            <p className="text-gray-400 text-xs mb-3">Meal Quality</p>
                            <div className="flex gap-6">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full bg-green-500" />
                                    <span className="text-white">{monthlyStats.meal_quality_breakdown.healthy}</span>
                                    <span className="text-gray-500 text-sm">Healthy</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                    <span className="text-white">{monthlyStats.meal_quality_breakdown.moderate}</span>
                                    <span className="text-gray-500 text-sm">Moderate</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full bg-red-500" />
                                    <span className="text-white">{monthlyStats.meal_quality_breakdown.unhealthy}</span>
                                    <span className="text-gray-500 text-sm">Unhealthy</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Recent History */}
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800">
                <h2 className="text-lg font-semibold text-white mb-4">Recent History</h2>
                <div className="space-y-2">
                    {recentLogs?.logs.map((log) => (
                        <div key={log.id} className="flex items-center justify-between bg-[#1e1e1e] rounded-lg p-3">
                            <div className="flex items-center gap-4">
                                <span className="text-gray-400 text-sm min-w-[80px]">
                                    {format(new Date(log.log_date), 'EEE, MMM d')}
                                </span>
                                <div className="flex gap-2">
                                    {log.exercises.filter(e => e.completed).map((e) => (
                                        <span key={e.exercise_type} className="text-sm">
                                            {EXERCISE_ICONS[e.exercise_type as keyof typeof EXERCISE_ICONS]}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-blue-400 text-sm">💧 {log.water_glasses}</span>
                                <span className={`px-2 py-1 rounded text-sm font-medium ${
                                    log.total_score >= 80 ? 'bg-green-500/20 text-green-400' :
                                    log.total_score >= 50 ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-red-500/20 text-red-400'
                                }`}>
                                    {log.total_score}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
```

### File: `frontend/src/components/notes/NotesLayout.tsx` (MODIFY)

Add the DailyTracker component. Modify the existing file:

```tsx
// Add this import at the top
import DailyTracker from '../habits/DailyTracker';

// Then modify the return statement to conditionally render DailyTracker
// when selectedFolder is 'daily-tracker':

// Find the part where NotesFeed and NoteEditor are rendered (around line 67-85)
// Replace with:

return (
    <div className="flex h-screen bg-[#121212] text-white overflow-hidden">
        {/* A. Left Pane - Sidebar */}
        <Sidebar
            selectedFolder={selectedFolder}
            selectedTag={selectedTag}
            onFolderChange={handleFolderChange}
            onTagClick={handleTagClick}
            onNewNote={handleNewNote}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />

        {/* Conditional rendering based on selectedFolder */}
        {selectedFolder === 'daily-tracker' ? (
            <DailyTracker />
        ) : selectedFolder === 'health-log' ? (
            // Health Log can show the reports view directly
            <DailyTracker initialDate={undefined} />
        ) : (
            <>
                {/* B. Feed - Notes List (~320px) */}
                <NotesFeed
                    selectedFolder={selectedFolder}
                    selectedTag={selectedTag}
                    selectedNoteId={selectedNoteId}
                    onNoteSelect={handleNoteSelect}
                />

                {/* C. Editor - Note Content (remaining width) */}
                <NoteEditor
                    noteId={selectedNoteId}
                    isEditing={isEditing}
                    onEditToggle={() => setIsEditing(!isEditing)}
                    onNoteCreated={handleNoteCreated}
                    onNoteDeleted={handleNoteDeleted}
                    initialTags={initialTags}
                    onNewNoteWithTags={handleNewNoteWithTags}
                    onLinkClick={handleNoteSelect}
                />
            </>
        )}
    </div>
);
```

---

## Part 4: Deployment Steps

### 1. Initialize Database Tables

After deploying the backend changes, run:

```bash
cd ~/notetracker
source venv/bin/activate
python -c "from api.init_habits_db import init_habits_tables; init_habits_tables()"
```

### 2. Restart Backend

```bash
# Kill existing process
pkill -f uvicorn

# Start new process
cd ~/notetracker
source venv/bin/activate
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
```

### 3. Rebuild Frontend

```bash
cd ~/notetracker/frontend
npm run build
```

### 4. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Test habits endpoint (replace with valid token)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/habits/today
```

---

## File Summary

### New Files to Create:

| File | Purpose |
|------|---------|
| `api/init_habits_db.py` | Database table initialization |
| `api/models/habits.py` | Pydantic models for habits |
| `api/routers/habits.py` | API endpoints for habits |
| `frontend/src/types/habits.ts` | TypeScript types |
| `frontend/src/api/habits.ts` | API client functions |
| `frontend/src/hooks/useHabits.ts` | React Query hooks |
| `frontend/src/components/habits/DailyTracker.tsx` | Main tracker component |
| `frontend/src/components/habits/HabitsReports.tsx` | Reports component |

### Files to Modify:

| File | Changes |
|------|---------|
| `api/main.py` | Add `habits_router` import and include |
| `frontend/src/components/notes/NotesLayout.tsx` | Add conditional rendering for DailyTracker |

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/habits/today` | Get today's log |
| GET | `/api/habits/date/{date}` | Get log by date |
| GET | `/api/habits` | List logs with filters |
| PUT | `/api/habits/date/{date}` | Update full daily log |
| PATCH | `/api/habits/exercise/{date}/{type}` | Toggle exercise |
| PATCH | `/api/habits/meal/{date}/{type}` | Toggle meal |
| PATCH | `/api/habits/water/{date}` | Update water |
| GET | `/api/habits/streak` | Get streak info |
| GET | `/api/habits/stats/weekly` | Get weekly stats |
| GET | `/api/habits/stats/monthly` | Get monthly stats |

---

## Testing Checklist

- [ ] Database tables created successfully
- [ ] API health check passes
- [ ] GET /api/habits/today returns empty log for new user
- [ ] PATCH exercise toggle works
- [ ] PATCH meal toggle works
- [ ] PATCH water update works
- [ ] GET streak returns correct values
- [ ] GET weekly stats returns data
- [ ] GET monthly stats returns data
- [ ] Frontend DailyTracker renders
- [ ] Checkbox toggles update UI immediately
- [ ] Date navigation works
- [ ] Reports tab shows stats
- [ ] Streak badge displays correctly
