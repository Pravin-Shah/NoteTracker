"""
Daily Habits Tracker API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import date, datetime, timedelta

from api.models.habits import (
    DailyLogCreate, DailyLogResponse, DailyLogListResponse,
    ExerciseEntryResponse, MealEntryResponse, SleepEntryResponse,
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
        log_id = results[0]['id']
        
        # Check if sleep entry exists (backfill for existing logs)
        sleep_check = execute_query(
            "SELECT id FROM sleep_entries WHERE daily_log_id = ?",
            (log_id,)
        )
        if not sleep_check:
            execute_insert(
                "INSERT INTO sleep_entries (daily_log_id, completed, hours, quality, energy) VALUES (?, 0, 0, 'Ok', 'Normal')",
                (log_id,)
            )
            
        return log_id

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

    # Initialize sleep entry
    execute_insert(
        "INSERT INTO sleep_entries (daily_log_id, completed, hours, quality, energy) VALUES (?, 0, 0, 'Ok', 'Normal')",
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


def get_sleep_for_log(log_id: int) -> Optional[SleepEntryResponse]:
    """Get sleep entry for a daily log."""
    results = execute_query(
        "SELECT * FROM sleep_entries WHERE daily_log_id = ?",
        (log_id,)
    )
    if not results:
        return None
    r = results[0]
    return SleepEntryResponse(
        id=r['id'],
        completed=bool(r.get('completed', 0)),
        hours=r['hours'],
        quality=r['quality'],
        energy=r['energy']
    )


def calculate_daily_score(exercises: list, meals: list, water_glasses: int, sleep: Optional[SleepEntryResponse] = None) -> dict:
    """Calculate daily scores."""
    exercise_completed = sum(1 for e in exercises if e.completed)
    healthy_meals = sum(1 for m in meals if m.completed and m.quality == 'healthy')
    meals_completed = sum(1 for m in meals if m.completed)

    # Score calculation (out of 100):
    # - Exercises: 35 points (5 per exercise type)
    # - Meals: 35 points (7 per meal)
    # - Water: 15 points (1.875 per glass, max 8)
    # - Sleep: 15 points (7.5 for 7+ hours, 4 for quality, 3.5 for energy)

    exercise_score = exercise_completed * 5  # Max 35
    meal_score = meals_completed * 7  # Max 35
    water_score = min(water_glasses * 1.875, 15)  # Max 15
    
    sleep_score = 0
    if sleep and sleep.completed:
        if sleep.hours >= 7: sleep_score += 7.5
        elif sleep.hours >= 5: sleep_score += 4
        
        if sleep.quality == 'Good': sleep_score += 4
        elif sleep.quality == 'Ok': sleep_score += 2
        
        if sleep.energy == 'Fresh': sleep_score += 3.5
        elif sleep.energy == 'Normal': sleep_score += 1.5

    total_score = int(exercise_score + meal_score + water_score + sleep_score)

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
    sleep = get_sleep_for_log(log_id)

    scores = calculate_daily_score(exercises, meals, water_glasses, sleep)

    return DailyLogResponse(
        id=log_id,
        user_id=log['user_id'],
        log_date=date.fromisoformat(log['log_date']),
        exercises=exercises,
        meals=meals,
        water_glasses=water_glasses,
        sleep=sleep,
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

    # Update sleep
    if log_data.sleep:
        execute_update(
            "UPDATE sleep_entries SET completed = ?, hours = ?, quality = ?, energy = ? WHERE daily_log_id = ?",
            (1 if log_data.sleep.completed else 0, log_data.sleep.hours, log_data.sleep.quality, log_data.sleep.energy, log_id)
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


@router.patch("/sleep/{log_date}")
async def update_sleep(
    log_date: date,
    completed: bool = Query(True),
    hours: float = Query(..., ge=0, le=24),
    quality: Optional[str] = Query(None),
    energy: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Update sleep for a day."""
    user_id = current_user['id']
    log_id = get_or_create_daily_log(user_id, log_date)

    execute_update(
        """UPDATE sleep_entries 
           SET completed = ?, hours = ?, quality = COALESCE(?, quality), energy = COALESCE(?, energy)
           WHERE daily_log_id = ?""",
        (1 if completed else 0, hours, quality, energy, log_id)
    )

    execute_update(
        "UPDATE daily_logs SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), log_id)
    )

    return {"status": "success", "hours": hours, "quality": quality, "energy": energy}


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
        sleep = get_sleep_for_log(log['id'])

        total_exercises += sum(1 for e in exercises if e.completed)
        total_healthy_meals += sum(1 for m in meals if m.completed and m.quality == 'healthy')
        total_water += water

        scores = calculate_daily_score(exercises, meals, water, sleep)
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
        sleep = get_sleep_for_log(log['id'])
        scores = calculate_daily_score(exercises, meals, water, sleep)
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
