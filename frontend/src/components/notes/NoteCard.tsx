import { useState } from 'react';
import type { Note } from '../../types/note';
import { notesApi } from '../../api/notes';
import ImageGallery from './ImageGallery';

interface NoteCardProps {
    note: Note;
    onUpdate: () => void;
}

export default function NoteCard({ note, onUpdate }: NoteCardProps) {
    const [showGallery, setShowGallery] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handlePin = async () => {
        try {
            await notesApi.togglePin(note.id, !note.pinned);
            onUpdate();
        } catch (error) {
            console.error('Failed to toggle pin:', error);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this note?')) return;

        setIsDeleting(true);
        try {
            await notesApi.delete(note.id);
            onUpdate();
        } catch (error) {
            console.error('Failed to delete note:', error);
            setIsDeleting(false);
        }
    };

    const importanceStars = '⭐'.repeat(note.importance);
    const hasImages = note.attachments && note.attachments.length > 0;
    const firstImage = hasImages ? note.attachments[0] : null;

    return (
        <>
            <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
                {/* Thumbnail Image */}
                {firstImage && (
                    <div className="relative h-48 bg-gray-100">
                        <img
                            src={`/uploads/${firstImage.file_path}`}
                            alt="Note thumbnail"
                            className="w-full h-full object-cover cursor-pointer"
                            onClick={() => setShowGallery(true)}
                        />
                        {note.attachments.length > 1 && (
                            <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-sm">
                                📷 +{note.attachments.length - 1} more
                            </div>
                        )}
                    </div>
                )}

                {/* Card Content */}
                <div className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 flex-1">
                            {note.title}
                        </h3>
                        <div className="flex items-center gap-1 ml-2">
                            <button
                                onClick={handlePin}
                                className="text-gray-400 hover:text-yellow-500 transition-colors"
                                title={note.pinned ? 'Unpin' : 'Pin'}
                            >
                                {note.pinned ? '📍' : '📌'}
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={isDeleting}
                                className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                                title="Delete"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>

                    {/* Importance */}
                    <div className="text-sm text-yellow-500 mb-2">{importanceStars}</div>

                    {/* Content Preview */}
                    {note.content && (
                        <p className="text-gray-600 text-sm mb-3 line-clamp-3">
                            {note.content.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ')}
                        </p>
                    )}

                    {/* Tags */}
                    {note.tags && note.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                            {note.tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                                >
                                    #{tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Footer */}
                    <div className="flex items-center justify-between text-xs text-gray-500 mt-3 pt-3 border-t">
                        <span>{note.category || 'Uncategorized'}</span>
                        {note.last_updated && (
                            <span>{new Date(note.last_updated).toLocaleDateString()}</span>
                        )}
                    </div>

                    {/* Gallery Button (if no thumbnail but has images) */}
                    {!firstImage && hasImages && (
                        <button
                            onClick={() => setShowGallery(true)}
                            className="mt-2 w-full text-sm text-blue-600 hover:text-blue-800"
                        >
                            🖼️ View {note.attachments.length} image{note.attachments.length > 1 ? 's' : ''}
                        </button>
                    )}
                </div>
            </div>

            {/* Image Gallery Modal */}
            {showGallery && hasImages && (
                <ImageGallery
                    images={note.attachments}
                    onClose={() => setShowGallery(false)}
                />
            )}
        </>
    );
}
