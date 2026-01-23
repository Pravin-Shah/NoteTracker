import { useState } from 'react';
import { format } from 'date-fns';
import {
    useTodayLog,
    useLogByDate,
    useToggleExercise,
    useToggleMeal,
    useUpdateWater,
    useUpdateSleep,
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
    type PortionSize,
    type SleepQuality,
    type MorningEnergy
} from '../../types/habits';
import HabitsReports from './HabitsReports';

interface DailyTrackerProps {
    initialDate?: string;
    initialTab?: 'today' | 'reports';
}

export default function DailyTracker({ initialDate, initialTab = 'today' }: DailyTrackerProps) {
    const [selectedDate, setSelectedDate] = useState(initialDate || format(new Date(), 'yyyy-MM-dd'));
    const [activeTab, setActiveTab] = useState<'today' | 'reports'>(initialTab);
    const [expandedExercise, setExpandedExercise] = useState<ExerciseType | null>(null);
    const [expandedMeal, setExpandedMeal] = useState<MealType | null>(null);

    const isToday = selectedDate === format(new Date(), 'yyyy-MM-dd');

    // Use conditional query based on whether it's today or not
    const todayLogQuery = useTodayLog();
    const dateLogQuery = useLogByDate(selectedDate);

    const { data: log, isLoading } = isToday ? todayLogQuery : dateLogQuery;
    const { data: streak } = useStreak();

    const toggleExercise = useToggleExercise();
    const toggleMeal = useToggleMeal();
    const updateWater = useUpdateWater();
    const updateSleep = useUpdateSleep();

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
        // Removed setExpandedExercise(null) to keep section open
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
        // Removed setExpandedMeal(null) to keep section open
    };

    const handleWaterChange = (delta: number) => {
        const currentGlasses = log?.water_glasses || 0;
        const newGlasses = Math.max(0, Math.min(20, currentGlasses + delta));
        updateWater.mutate({ date: selectedDate, glasses: newGlasses });
    };

    const handleSleepUpdate = (hours: number, quality?: SleepQuality, energy?: MorningEnergy) => {
        updateSleep.mutate({
            date: selectedDate,
            completed: true,
            hours,
            quality,
            energy
        });
    };

    const handleSleepToggle = (currentCompleted: boolean) => {
        const sleep = log?.sleep;
        updateSleep.mutate({
            date: selectedDate,
            completed: !currentCompleted,
            hours: !currentCompleted && (!sleep?.hours || sleep.hours === 0) ? 8 : (sleep?.hours || 0),
            quality: sleep?.quality || 'Ok',
            energy: sleep?.energy || 'Normal'
        });
    };

    if (isLoading) {
        return (
            <div className="flex-1 bg-[#1e1e1e] flex items-center justify-center">
                <div className="text-gray-500">Loading...</div>
            </div>
        );
    }

    return (
        <div className="flex-1 bg-[#1e1e1e] flex flex-col overflow-hidden" style={{ paddingLeft: '0.5rem' }}>
            {/* Header */}
            <div className="bg-[#252525] border-b border-gray-800 py-4" style={{ paddingLeft: '1.5rem', paddingRight: '1.5rem' }}>
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
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'today'
                                ? 'bg-blue-600 text-white'
                                : 'bg-[#333] text-gray-400 hover:text-white'
                                }`}
                        >
                            Today
                        </button>
                        <button
                            onClick={() => setActiveTab('reports')}
                            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'reports'
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
            <div className="flex-1 overflow-y-auto p-6" style={{ paddingLeft: '1.5rem' }}>
                {activeTab === 'today' ? (
                    <div className="max-w-2xl mx-auto" style={{ paddingTop: '0.25rem', paddingBottom: '1rem' }}>
                        {/* Score Summary */}
                        {log && (
                            <div className="bg-[#252525] rounded-xl p-4 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-400 text-sm">Daily Score</span>
                                    <span className={`text-2xl font-bold ${log.total_score >= 80 ? 'text-green-400' :
                                        log.total_score >= 50 ? 'text-yellow-400' :
                                            'text-red-400'
                                        }`}>
                                        {log.total_score}/100
                                    </span>
                                </div>
                                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all duration-500 ${log.total_score >= 80 ? 'bg-green-500' :
                                            log.total_score >= 50 ? 'bg-yellow-500' :
                                                'bg-red-500'
                                            }`}
                                        style={{ width: `${log.total_score}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Exercise Section */}
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                🏋️ Exercise
                            </h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {(['hip_exercises', 'upper_body', 'walk', 'yoga', 'eye_exercises', 'meditation', 'cardio', 'sleep'] as (ExerciseType | 'sleep')[]).map((type) => {
                                    if (type === 'sleep') {
                                        const sleep = log?.sleep;
                                        const isExpanded = (expandedExercise as string) === 'sleep';

                                        return (
                                            <div key="sleep" className="bg-[#1e1e1e] rounded-lg p-3">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <button
                                                            onClick={() => handleSleepToggle(sleep?.completed || false)}
                                                            className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${sleep?.completed
                                                                ? 'bg-indigo-500 border-indigo-500 text-white'
                                                                : 'border-gray-600 hover:border-gray-500'
                                                                }`}
                                                        >
                                                            {sleep?.completed && '✓'}
                                                        </button>
                                                        <span className="text-lg">💤</span>
                                                        <span className="text-white">Sleep</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {sleep?.completed && sleep?.hours > 0 && (
                                                            <span className="text-sm text-gray-400">
                                                                {sleep.hours} hrs
                                                            </span>
                                                        )}
                                                        <button
                                                            onClick={() => setExpandedExercise(isExpanded ? null : 'sleep' as any)}
                                                            className="p-1 hover:bg-[#333] rounded text-gray-400"
                                                        >
                                                            {isExpanded ? '▲' : '▼'}
                                                        </button>
                                                    </div>
                                                </div>

                                                {isExpanded && (
                                                    <div className="mt-3 pt-3 border-t border-gray-700 space-y-4">
                                                        <div>
                                                            <label className="text-sm text-gray-400 block mb-2">Sleep Hours:</label>
                                                            <div className="flex items-center gap-4">
                                                                <input
                                                                    type="range"
                                                                    min="0"
                                                                    max="12"
                                                                    step="0.5"
                                                                    value={sleep?.hours || 0}
                                                                    onChange={(e) => handleSleepUpdate(parseFloat(e.target.value), sleep?.quality || 'Ok', sleep?.energy || 'Normal')}
                                                                    className="flex-1 accent-indigo-500"
                                                                />
                                                                <input
                                                                    type="number"
                                                                    value={sleep?.hours || 0}
                                                                    onChange={(e) => handleSleepUpdate(parseFloat(e.target.value) || 0, sleep?.quality || 'Ok', sleep?.energy || 'Normal')}
                                                                    className="w-16 bg-[#333] text-white px-2 py-1 rounded text-center border border-gray-700"
                                                                />
                                                                <span className="text-sm text-gray-500">hrs</span>
                                                            </div>
                                                        </div>

                                                        <div>
                                                            <label className="text-sm text-gray-400 block mb-2">Sleep Quality:</label>
                                                            <div className="flex gap-2">
                                                                {(['Good', 'Ok', 'Bad'] as SleepQuality[]).map((q) => (
                                                                    <button
                                                                        key={q}
                                                                        onClick={() => handleSleepUpdate(sleep?.hours || 0, q, sleep?.energy || 'Normal')}
                                                                        className={`px-3 py-1.5 rounded text-sm transition-colors ${sleep?.quality === q
                                                                            ? 'bg-indigo-500 text-white'
                                                                            : 'bg-[#333] text-gray-400 hover:text-white'
                                                                            }`}
                                                                    >
                                                                        {q === 'Good' ? '✅ Good' : q === 'Ok' ? '😐 Ok' : '😴 Bad'}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>

                                                        <div>
                                                            <label className="text-sm text-gray-400 block mb-2">Morning Energy:</label>
                                                            <div className="flex gap-2">
                                                                {(['Fresh', 'Normal', 'Tired'] as MorningEnergy[]).map((e) => (
                                                                    <button
                                                                        key={e}
                                                                        onClick={() => handleSleepUpdate(sleep?.hours || 0, sleep?.quality || 'Ok', e)}
                                                                        className={`px-3 py-1.5 rounded text-sm transition-colors ${sleep?.energy === e
                                                                            ? 'bg-orange-500 text-white'
                                                                            : 'bg-[#333] text-gray-400 hover:text-white'
                                                                            }`}
                                                                    >
                                                                        {e === 'Fresh' ? '⚡ Fresh' : e === 'Normal' ? '😐 Normal' : '🥱 Tired'}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    }

                                    const exercise = log?.exercises.find(e => e.exercise_type === type);
                                    const isExpanded = expandedExercise === type;

                                    return (
                                        <div key={type} className="bg-[#1e1e1e] rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={() => handleExerciseToggle(type, exercise?.completed || false)}
                                                        className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${exercise?.completed
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
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                🍽️ Meals
                            </h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {(['breakfast', 'lunch', 'evening_snack', 'dinner', 'night_snack'] as MealType[]).map((type) => {
                                    const meal = log?.meals.find(m => m.meal_type === type);
                                    const isExpanded = expandedMeal === type;

                                    return (
                                        <div key={type} className="bg-[#1e1e1e] rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={() => handleMealToggle(type, meal?.completed || false, meal?.quality as MealQuality)}
                                                        className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${meal?.completed
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
                                                                    className={`px-3 py-1.5 rounded text-sm capitalize transition-colors ${meal?.quality === q
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
                                                                    className={`px-3 py-1.5 rounded text-sm capitalize transition-colors ${meal?.portion_size === size
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
                                                            className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${meal?.has_protein
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
                        <div className="bg-[#252525] rounded-xl p-4 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
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
                                            className={`w-4 h-8 rounded-sm transition-colors ${i < (log?.water_glasses || 0)
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
