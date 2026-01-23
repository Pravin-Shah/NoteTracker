import { useState } from 'react';
import { format } from 'date-fns';
import { useWeeklyStats, useMonthlyStats, useStreak, useHabitsLogs } from '../../hooks/useHabits';
import { EXERCISE_LABELS, EXERCISE_ICONS, type ExerciseType } from '../../types/habits';

export default function HabitsReports() {
    const [weekOffset, setWeekOffset] = useState(0);
    const [monthOffset, setMonthOffset] = useState(0);

    const { data: streak } = useStreak();
    const { data: weeklyStats, isLoading: weeklyLoading } = useWeeklyStats(weekOffset);
    const { data: monthlyStats, isLoading: monthlyLoading } = useMonthlyStats(monthOffset);

    // Get recent logs for history
    const { data: recentLogs } = useHabitsLogs({ limit: 7 });

    return (
        <div className="max-w-4xl mx-auto" style={{ paddingTop: '0.5rem', paddingBottom: '1rem' }}>
            {/* Streak Cards */}
            <div className="grid grid-cols-2 gap-4" style={{ marginBottom: '0.5rem' }}>
                <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/10 rounded-xl p-5 border border-orange-500/30">
                    <div className="flex flex-col items-center justify-center gap-2 mb-2">
                        <span className="text-2xl">🔥</span>
                        <span className="text-orange-400 text-sm font-medium">Current Streak</span>
                    </div>
                    <p className="text-4xl font-bold text-white text-center">
                        {streak?.current_streak || 0}
                        <span className="text-lg text-gray-400 ml-2">days</span>
                    </p>
                </div>

                <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 rounded-xl p-5 border border-purple-500/30">
                    <div className="flex flex-col items-center justify-center gap-2 mb-2">
                        <span className="text-2xl">🏆</span>
                        <span className="text-purple-400 text-sm font-medium">Best Streak</span>
                    </div>
                    <p className="text-4xl font-bold text-white text-center">
                        {streak?.best_streak || 0}
                        <span className="text-lg text-gray-400 ml-2">days</span>
                    </p>
                </div>
            </div>

            {/* Weekly Stats */}
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
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
                            <p className={`text-2xl font-bold ${weeklyStats.average_daily_score >= 80 ? 'text-green-400' :
                                weeklyStats.average_daily_score >= 50 ? 'text-yellow-400' :
                                    'text-red-400'
                                }`}>{weeklyStats.average_daily_score}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Monthly Stats */}
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
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
                        <div className="bg-[#1e1e1e] rounded-lg p-4" style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
                            <p className="text-gray-400 text-xs mb-3">Exercise Breakdown</p>
                            <div className="flex flex-wrap gap-4">
                                {Object.entries(monthlyStats.exercise_breakdown).map(([type, count]) => (
                                    <div key={type} className="flex items-center gap-2">
                                        <span>{EXERCISE_ICONS[type as ExerciseType]}</span>
                                        <span className="text-white">{count}</span>
                                        <span className="text-gray-500 text-sm">{EXERCISE_LABELS[type as ExerciseType]}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Meal Quality Breakdown */}
                        <div className="bg-[#1e1e1e] rounded-lg p-4" style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>
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
            <div className="bg-[#252525] rounded-xl p-5 border border-gray-800" style={{ marginBottom: '0.5rem' }}>
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
                                            {EXERCISE_ICONS[e.exercise_type as ExerciseType]}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {log.sleep && log.sleep.hours > 0 && (
                                    <span className="text-indigo-400 text-sm">💤 {log.sleep.hours}h</span>
                                )}
                                <span className="text-blue-400 text-sm">💧 {log.water_glasses}</span>
                                <span className={`px-2 py-1 rounded text-sm font-medium ${log.total_score >= 80 ? 'bg-green-500/20 text-green-400' :
                                    log.total_score >= 50 ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                                    }`}>
                                    {log.total_score}
                                </span>
                            </div>
                        </div>
                    ))}
                    {(!recentLogs?.logs || recentLogs.logs.length === 0) && (
                        <div className="text-center text-gray-500 py-8">
                            No logs yet. Start tracking your habits!
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
