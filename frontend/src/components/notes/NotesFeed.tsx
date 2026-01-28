import { useState, useEffect } from 'react';
import { useNotes } from '../../hooks/useNotes';
import { formatDistanceToNow } from 'date-fns';

interface NotesFeedProps {
    selectedFolder: string;
    selectedTag: string | null;
    selectedNoteId: number | null;
    onNoteSelect: (noteId: number) => void;
}

export default function NotesFeed({
    selectedFolder,
    selectedTag,
    selectedNoteId,
    onNoteSelect,
}: NotesFeedProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');

    // Debounce search query to prevent cursor jumping
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedQuery(searchQuery);
        }, 600);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    // Build filters based on selected folder/tag/search
    const filters = {
        query: debouncedQuery || undefined,
        tag: selectedTag || undefined,
        archived: selectedFolder === 'trash',
        pinned_only: selectedFolder === 'favorites',
    };

    const { notes, loading } = useNotes(filters);

    if (loading) {
        return (
            <div className="w-80 bg-[#1e1e1e] border-r border-gray-800 flex items-center justify-center">
                <div className="text-gray-500 text-sm">Loading...</div>
            </div>
        );
    }

    return (
        <div className="w-80 bg-[#1e1e1e] border-r border-gray-800 flex flex-col">
            {/* Search Bar */}
            <div className="py-3" style={{ paddingLeft: '0.5rem', paddingRight: '0.25rem' }}>
                <div className="relative" style={{ paddingTop: '0.5rem', paddingBottom: '0.75rem' }}>
                    <input
                        type="text"
                        placeholder="Search notes..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-[#2a2a2a] text-white placeholder-gray-500 px-3 py-2 pr-9 rounded-md text-[13px] focus:outline-none focus:ring-1 focus:ring-gray-600 border border-gray-700"
                    />
                    <svg
                        className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                </div>
            </div>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto" style={{ paddingTop: '0.1rem', paddingBottom: '0.5rem' }}>
                {notes.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 text-sm">
                        No notes found
                    </div>
                ) : (
                    <div className="px-2 pb-2 flex flex-col" style={{ gap: '0.75rem' }}>
                        {notes.map((note) => {
                            const hasAttachments = note.attachments && note.attachments.length > 0;
                            // Prefer image attachment for thumbnail, fall back to first attachment
                            const imageAttachment = note.attachments?.find(a => a.file_type === 'image');
                            const thumbnail = imageAttachment || (hasAttachments ? note.attachments[0] : null);
                            const isSelected = note.id === selectedNoteId;

                            return (
                                <button
                                    key={note.id}
                                    onClick={() => onNoteSelect(note.id)}
                                    className={`w-full text-left p-2.5 rounded-lg transition-colors ${isSelected
                                        ? 'bg-[#2a2a2a] ring-1 ring-gray-700'
                                        : 'hover:bg-[#252525]'
                                        }`}
                                    style={{ paddingLeft: '0.25rem', paddingRight: '0.5rem' }}
                                >
                                    <div className="flex gap-2.5">
                                        {/* Thumbnail or Placeholder */}
                                        <div className="flex-shrink-0 w-11 h-11 rounded-md overflow-hidden bg-gray-700 flex items-center justify-center">
                                            {thumbnail && thumbnail.file_type === 'image' ? (
                                                <img
                                                    src={`/uploads/${thumbnail.file_path}`}
                                                    alt=""
                                                    className="w-full h-full object-cover"
                                                    onError={(e) => {
                                                        const target = e.target as HTMLImageElement;
                                                        target.style.display = 'none';
                                                    }}
                                                />
                                            ) : hasAttachments ? (
                                                /* Has attachments but first one is not an image - show file icon */
                                                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                </svg>
                                            ) : (
                                                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                </svg>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            {/* Title and Time */}
                                            <div className="flex items-start justify-between gap-2 mb-0.5">
                                                <h3 className="font-medium text-[13px] text-white truncate flex-1 leading-snug">
                                                    {note.title}
                                                </h3>
                                                <span className="text-[10px] text-gray-500 flex-shrink-0 pt-0.5">
                                                    {note.last_updated &&
                                                        formatDistanceToNow(new Date(note.last_updated), {
                                                            addSuffix: false,
                                                        }).replace('about ', '').replace(' hours', 'h').replace(' hour', 'h').replace(' minutes', 'm').replace(' minute', 'm').replace(' days', 'd').replace(' day', 'd')}
                                                </span>
                                            </div>

                                            {/* Preview Text */}
                                            <p className="text-[12px] text-gray-500 line-clamp-2 leading-snug">
                                                {note.content ? note.content.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ') : 'No content'}
                                            </p>

                                            {/* Tags */}
                                            {note.tags && note.tags.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-1.5">
                                                    {note.tags.slice(0, 3).map((tag) => (
                                                        <span
                                                            key={tag}
                                                            className="text-[10px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded"
                                                        >
                                                            #{tag}
                                                        </span>
                                                    ))}
                                                    {note.tags.length > 3 && (
                                                        <span className="text-[10px] text-gray-500">
                                                            +{note.tags.length - 3}
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
