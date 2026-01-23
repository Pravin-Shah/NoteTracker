import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { habitsApi } from '../api/habits';
import type {
    DailyLogCreate,
    HabitsFilter,
    ExerciseType,
    MealType,
    MealQuality,
    PortionSize,
    SleepQuality,
    MorningEnergy
} from '../types/habits';

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

// Update sleep mutation
export function useUpdateSleep() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            date,
            completed,
            hours,
            quality,
            energy
        }: {
            date: string;
            completed: boolean;
            hours: number;
            quality?: SleepQuality;
            energy?: MorningEnergy
        }) => habitsApi.updateSleep(date, completed, hours, quality, energy),
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
