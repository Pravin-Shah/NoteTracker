import { useState } from 'react';
import NotesList from './NotesList';
import NoteForm from './NoteForm';

export default function NotesPage() {
    const [showCreateForm, setShowCreateForm] = useState(false);

    const handleCreateSuccess = () => {
        setShowCreateForm(false);
        // The list will auto-refresh via React Query
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-gray-900">📝 Notes</h1>
                <button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    {showCreateForm ? '❌ Cancel' : '➕ New Note'}
                </button>
            </div>

            {/* Create Form */}
            {showCreateForm && (
                <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4">Create New Note</h2>
                    <NoteForm
                        onSuccess={handleCreateSuccess}
                        onCancel={() => setShowCreateForm(false)}
                    />
                </div>
            )}

            {/* Notes List */}
            <NotesList />
        </div>
    );
}
