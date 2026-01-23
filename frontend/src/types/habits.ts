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

// Sleep types
export type SleepQuality = 'Good' | 'Ok' | 'Bad';
export type MorningEnergy = 'Fresh' | 'Normal' | 'Tired';

export interface SleepEntry {
    id?: number;
    completed: boolean;
    hours: number;
    quality: SleepQuality;
    energy: MorningEnergy;
}

// Daily log
export interface DailyLog {
    id: number;
    user_id: number;
    log_date: string;  // ISO date string
    exercises: ExerciseEntry[];
    meals: MealEntry[];
    water_glasses: number;
    sleep?: SleepEntry | null;
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
    sleep?: SleepEntry | null;
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
