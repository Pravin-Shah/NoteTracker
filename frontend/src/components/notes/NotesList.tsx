import { useState } from 'react';
import NoteCard from './NoteCard';
import NoteFilters from './NoteFilters';
import { useNotes } from '../../hooks/useNotes';

export default function NotesList() {
    const [filters, setFilters] = useState({
        query: '',
        category: undefined,
        tag: undefined,
        importance: undefined,
        archived: false,
        pinned_only: false,
    });

    const { notes, loading, error, refetch } = useNotes(filters);

    const handleFilterChange = (newFilters: any) => {
        setFilters({ ...filters, ...newFilters });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                Error loading notes: {error.message}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <NoteFilters filters={filters} onFilterChange={handleFilterChange} />

            {notes.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <p className="text-lg">No notes found</p>
                    <p className="text-sm mt-2">Create your first note to get started!</p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {notes.map((note) => (
                        <NoteCard key={note.id} note={note} onUpdate={refetch} />
                    ))}
                </div>
            )}
        </div>
    );
}
