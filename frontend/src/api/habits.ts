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
    PortionSize,
    SleepQuality,
    MorningEnergy
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

    // Update sleep
    async updateSleep(
        date: string,
        completed: boolean,
        hours: number,
        quality?: SleepQuality,
        energy?: MorningEnergy
    ): Promise<void> {
        const params = new URLSearchParams();
        params.append('completed', completed.toString());
        params.append('hours', hours.toString());
        if (quality) params.append('quality', quality);
        if (energy) params.append('energy', energy);

        await api.patch(`/api/habits/sleep/${date}?${params.toString()}`);
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
