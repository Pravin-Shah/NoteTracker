import type { NoteFilter } from '../../types/note';

interface NoteFiltersProps {
    filters: NoteFilter;
    onFilterChange: (filters: Partial<NoteFilter>) => void;
}

export default function NoteFilters({ filters, onFilterChange }: NoteFiltersProps) {
    return (
        <div className="bg-white rounded-lg shadow p-4 space-y-4">
            {/* Search */}
            <div>
                <input
                    type="text"
                    value={filters.query || ''}
                    onChange={(e) => onFilterChange({ query: e.target.value })}
                    placeholder="Search notes..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>

            {/* Filters Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {/* Category Filter */}
                <select
                    value={filters.category || ''}
                    onChange={(e) =>
                        onFilterChange({ category: e.target.value || undefined })
                    }
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Categories</option>
                    <option value="personal">Personal</option>
                    <option value="work">Work</option>
                    <option value="ideas">Ideas</option>
                    <option value="reference">Reference</option>
                    <option value="other">Other</option>
                </select>

                {/* Importance Filter */}
                <select
                    value={filters.importance || ''}
                    onChange={(e) =>
                        onFilterChange({
                            importance: e.target.value ? parseInt(e.target.value) : undefined,
                        })
                    }
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Importance</option>
                    <option value="1">⭐ (1)</option>
                    <option value="2">⭐⭐ (2)</option>
                    <option value="3">⭐⭐⭐ (3)</option>
                    <option value="4">⭐⭐⭐⭐ (4)</option>
                    <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                </select>

                {/* Pinned Only */}
                <label className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                        type="checkbox"
                        checked={filters.pinned_only || false}
                        onChange={(e) => onFilterChange({ pinned_only: e.target.checked })}
                        className="rounded"
                    />
                    <span className="text-sm">📌 Pinned Only</span>
                </label>

                {/* Archived */}
                <label className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                        type="checkbox"
                        checked={filters.archived || false}
                        onChange={(e) => onFilterChange({ archived: e.target.checked })}
                        className="rounded"
                    />
                    <span className="text-sm">📦 Show Archived</span>
                </label>
            </div>
        </div>
    );
}
