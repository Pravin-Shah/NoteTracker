import { useState, useRef, useEffect } from 'react';
import { useNote } from '../../hooks/useNotes';
import { notesApi } from '../../api/notes';
import ImageGallery from './ImageGallery';
import FileAttachment from './FileAttachment';
import { useQueryClient } from '@tanstack/react-query';
import RichTextEditor from './RichTextEditor';
import './tiptap.css';

interface NoteEditorProps {
    noteId: number | null;
    isEditing: boolean;
    onEditToggle: () => void;
    onNoteCreated?: (noteId: number) => void;
    onNoteDeleted?: () => void;
    initialTags?: string[];
    onNewNoteWithTags?: (tags: string[]) => void;
}

export default function NoteEditor({ noteId, isEditing, onEditToggle, onNoteCreated, onNoteDeleted, initialTags = [], onNewNoteWithTags }: NoteEditorProps) {
    const queryClient = useQueryClient();
    const { data: note, isLoading } = useNote(noteId);
    const isCreating = !noteId && isEditing;
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [tags, setTags] = useState<string[]>([]);
    const [showGallery, setShowGallery] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [tagInput, setTagInput] = useState('');
    const [linkCopied, setLinkCopied] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleCopyLink = async () => {
        if (!note) return;
        const linkText = `[[${note.title}|${note.id}]]`;

        try {
            // Try modern clipboard API first (requires HTTPS)
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(linkText);
            } else {
                // Fallback for HTTP: use textarea trick
                const textArea = document.createElement('textarea');
                textArea.value = linkText;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy link:', err);
            // Show the link in a prompt as last resort
            prompt('Copy this link:', linkText);
        }
    };



    const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
            e.preventDefault();
            const newTags = tagInput
                .split(',')
                .map(t => t.trim().toLowerCase().replace(/^#/, ''))
                .filter(t => t && !tags.includes(t));
            if (newTags.length > 0) {
                setTags([...tags, ...newTags]);
            }
            setTagInput('');
        }
    };

    const handleRemoveTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    // Update local state when note changes or when creating new note
    useEffect(() => {
        if (note) {
            setTitle(note.title);
            setContent(note.content);
            setTags(note.tags || []);
        } else if (isCreating) {
            setTitle('');
            setContent('');
            setTags(initialTags);
            setTagInput('');
        }
    }, [note, isCreating, initialTags]);

    const handleSave = async () => {
        if (!title.trim()) {
            alert('Please enter a title');
            return;
        }

        try {
            if (isCreating) {
                // Create new note
                const newNote = await notesApi.create({
                    title,
                    content,
                    tags,
                });
                await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
                onNoteCreated?.(newNote.id);
            } else if (noteId) {
                // Update existing note
                await notesApi.update(noteId, {
                    title,
                    content,
                    tags,
                });
                await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', noteId] });
                await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
                onEditToggle();
            }
        } catch (error) {
            console.error('Failed to save note:', error);
        }
    };

    const handleDelete = async () => {
        if (!noteId) return;

        if (!confirm('Are you sure you want to delete this note?')) return;

        try {
            await notesApi.delete(noteId);
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
            onNoteDeleted?.();
        } catch (error) {
            console.error('Failed to delete note:', error);
        }
    };

    const handleToggleFavorite = async () => {
        if (!noteId || !note) return;
        try {
            await notesApi.togglePin(noteId, !note.pinned);
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
            await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', noteId] });
        } catch (error) {
            console.error('Failed to toggle favorite:', error);
        }
    };

    const handleRestore = async () => {
        if (!noteId) return;
        try {
            await notesApi.toggleArchive(noteId, false);
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
            await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', noteId] });
        } catch (error) {
            console.error('Failed to restore note:', error);
        }
    };

    const handlePermanentDelete = async () => {
        if (!noteId) return;
        if (!confirm('This will permanently delete the note. This cannot be undone. Are you sure?')) return;
        try {
            await notesApi.permanentDelete(noteId);
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
            onNoteDeleted?.();
        } catch (error) {
            console.error('Failed to permanently delete note:', error);
        }
    };

    // Helper function to auto-save note and return the new note ID
    const autoSaveNote = async (): Promise<number | null> => {
        try {
            const noteTitle = title.trim() || 'Untitled Note';
            const newNote = await notesApi.create({
                title: noteTitle,
                content,
                tags,
            });
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
            return newNote.id;
        } catch (error) {
            console.error('Failed to auto-save note:', error);
            return null;
        }
    };

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;

        const files = Array.from(e.target.files);
        setIsUploading(true);

        try {
            let targetNoteId = noteId;

            // If we're creating a new note, auto-save it first
            if (isCreating) {
                const newNoteId = await autoSaveNote();
                if (!newNoteId) {
                    setIsUploading(false);
                    return;
                }
                targetNoteId = newNoteId;
                // Notify parent that note was created so it can switch to edit mode
                onNoteCreated?.(newNoteId);
            }

            if (!targetNoteId) {
                setIsUploading(false);
                return;
            }

            await Promise.all(
                files.map((file) => notesApi.uploadAttachment(targetNoteId!, file))
            );
            // Invalidate and refetch the note data
            await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', targetNoteId] });
            await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
        } catch (error) {
            console.error('Failed to upload images:', error);
        } finally {
            setIsUploading(false);
        }
    };

    const handlePaste = async (e: React.ClipboardEvent) => {
        if (!isEditing && !isCreating) return;

        const items = e.clipboardData?.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                e.preventDefault(); // Prevent default paste behavior
                const file = items[i].getAsFile();
                if (file) {
                    setIsUploading(true);
                    try {
                        let targetNoteId = noteId;

                        // If we're creating a new note, auto-save it first
                        if (isCreating) {
                            const newNoteId = await autoSaveNote();
                            if (!newNoteId) {
                                setIsUploading(false);
                                return;
                            }
                            targetNoteId = newNoteId;
                            // Notify parent that note was created so it can switch to edit mode
                            onNoteCreated?.(newNoteId);
                        }

                        if (!targetNoteId) {
                            setIsUploading(false);
                            return;
                        }

                        await notesApi.uploadAttachment(targetNoteId, file);
                        // Invalidate and refetch the note data
                        await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', targetNoteId] });
                        await queryClient.invalidateQueries({ queryKey: ['notes', 'list'] });
                    } catch (error) {
                        console.error('Failed to upload pasted image:', error);
                    } finally {
                        setIsUploading(false);
                    }
                }
            }
        }
    };

    if (!noteId && !isCreating) {
        return (
            <div className="flex-1 bg-[#252525] flex items-center justify-center">
                <div className="text-center text-gray-500">
                    <svg className="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-sm">Select a note to view</p>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex-1 bg-[#252525] flex items-center justify-center">
                <div className="text-gray-500 text-sm">Loading...</div>
            </div>
        );
    }

    if (!note && !isCreating) {
        return (
            <div className="flex-1 bg-[#252525] flex items-center justify-center">
                <div className="text-red-400 text-sm">Note not found</div>
            </div>
        );
    }

    const hasImages = note?.attachments && note.attachments.length > 0;

    return (
        <div className="flex-1 bg-[#252525] flex flex-col">
            {/* Header */}
            <div className="bg-[#1e1e1e] border-b border-gray-800 px-8 py-5 flex items-center justify-between flex-shrink-0">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-[13px]" style={{ paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
                    <span className="text-gray-500">All Notes</span>
                    <span className="text-gray-600 mx-2">/</span>
                    <span className="text-white font-medium">{isCreating ? 'New Note' : note?.title}</span>
                </div>

                {/* Header Buttons */}
                <div className="flex items-center gap-2" style={{ marginRight: '2rem' }}>
                    {!isCreating && onNewNoteWithTags && (
                        <button
                            onClick={() => onNewNoteWithTags(note?.tags || [])}
                            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            New Note
                        </button>
                    )}
                    {!isCreating && (
                        <button
                            onClick={handleCopyLink}
                            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            {linkCopied ? 'Copied!' : 'Copy Link'}
                        </button>
                    )}
                    {!isCreating && Boolean(note?.archived) && (
                        <button
                            onClick={handleRestore}
                            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            Restore
                        </button>
                    )}
                    {!isCreating && Boolean(note?.archived) && (
                        <button
                            onClick={handlePermanentDelete}
                            className="px-4 py-2 bg-red-800 hover:bg-red-700 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            Permanently Delete
                        </button>
                    )}
                    {!isCreating && !Boolean(note?.archived) && (
                        <button
                            onClick={handleToggleFavorite}
                            className={`px-4 py-2 ${Boolean(note?.pinned) ? 'bg-yellow-600 hover:bg-yellow-500' : 'bg-gray-600 hover:bg-gray-500'} text-white text-[12px] font-medium rounded transition-colors`}
                        >
                            {Boolean(note?.pinned) ? 'Unfavorite' : 'Favorite'}
                        </button>
                    )}
                    {!isCreating && !Boolean(note?.archived) && (
                        <button
                            onClick={handleDelete}
                            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            Delete
                        </button>
                    )}
                    {!isCreating && (
                        <button
                            onClick={onEditToggle}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-[12px] font-medium rounded transition-colors"
                        >
                            {isEditing ? 'View' : 'Edit'}
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-3xl mx-auto py-10" style={{ paddingLeft: '3rem', paddingRight: '2rem' }}>
                    {(isEditing || isCreating) ? (
                        /* Edit Mode */
                        <div onPaste={handlePaste}>
                            {/* Title Input */}
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full bg-transparent text-2xl font-semibold text-white leading-tight border-none outline-none placeholder-gray-600"
                                style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}
                                placeholder="Note title"
                            />

                            {/* Metadata */}
                            <div className="text-[13px] text-gray-500 border-b border-gray-700" style={{ paddingBottom: '1rem', marginBottom: '0.75rem' }}>
                                {!isCreating && (
                                    <div className="flex items-center gap-6 mb-3">
                                        <span>Created: {note?.created_date && new Date(note.created_date).toLocaleDateString()}</span>
                                    </div>
                                )}
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-gray-500">Tags:</span>
                                    {tags.map(tag => (
                                        <span
                                            key={tag}
                                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-700 text-gray-300 rounded text-[12px]"
                                        >
                                            #{tag}
                                            <button
                                                onClick={() => handleRemoveTag(tag)}
                                                className="text-gray-500 hover:text-white ml-0.5"
                                            >
                                                ×
                                            </button>
                                        </span>
                                    ))}
                                    <input
                                        type="text"
                                        value={tagInput}
                                        onChange={(e) => setTagInput(e.target.value)}
                                        onKeyDown={handleAddTag}
                                        placeholder="Add tag..."
                                        className="bg-transparent border-none outline-none text-[12px] text-gray-400 placeholder-gray-600 w-20"
                                    />
                                </div>
                            </div>

                            {/* Content Editor */}
                            <div className="text-gray-900 bg-white rounded-lg overflow-hidden" style={{ minHeight: '300px' }}>
                                <RichTextEditor
                                    key={isCreating ? 'new-note' : noteId}
                                    content={content}
                                    onChange={setContent}
                                    placeholder="Start writing..."
                                />
                            </div>

                            {/* Attachments Section */}
                            {hasImages && note && (
                                <div className="border-t border-gray-700" style={{ marginTop: '1.5rem', paddingTop: '0.75rem' }}>
                                    <div className="flex items-center gap-2" style={{ marginBottom: '1.5rem' }}>
                                        <h3 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider">Attachments</h3>
                                        {isUploading && (
                                            <span className="text-[11px] text-blue-400">Uploading...</span>
                                        )}
                                    </div>

                                    {/* Images Grid */}
                                    {note.attachments.filter(a => a.file_type === 'image').length > 0 && (
                                        <div className="mb-4">
                                            <h4 className="text-[12px] text-gray-500 mb-2">Images</h4>
                                            <div className="grid grid-cols-4 gap-2">
                                                {note.attachments.filter(a => a.file_type === 'image').map((attachment) => (
                                                    <div key={attachment.id} className="relative group">
                                                        <img
                                                            src={`/uploads/${attachment.file_path}`}
                                                            alt=""
                                                            className="w-full h-24 object-cover rounded cursor-pointer"
                                                            onClick={() => setShowGallery(true)}
                                                            onError={(e) => {
                                                                const target = e.target as HTMLImageElement;
                                                                target.style.display = 'none';
                                                                target.parentElement?.classList.add('bg-gray-700', 'flex', 'items-center', 'justify-center');
                                                                const icon = document.createElement('span');
                                                                icon.textContent = '🖼️';
                                                                icon.className = 'text-2xl';
                                                                target.parentElement?.appendChild(icon);
                                                            }}
                                                        />
                                                        {/* Action buttons overlay */}
                                                        <div className="absolute bottom-1 left-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    window.open(`/uploads/${attachment.file_path}`, '_blank');
                                                                }}
                                                                className="flex-1 px-2 py-1 bg-blue-600/90 hover:bg-blue-500 text-white text-[10px] rounded transition-colors"
                                                                title="Open image"
                                                            >
                                                                Open
                                                            </button>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    const link = document.createElement('a');
                                                                    link.href = `/uploads/${attachment.file_path}`;
                                                                    link.download = attachment.original_filename || attachment.file_path;
                                                                    document.body.appendChild(link);
                                                                    link.click();
                                                                    document.body.removeChild(link);
                                                                }}
                                                                className="px-2 py-1 bg-gray-600/90 hover:bg-gray-500 text-white text-[10px] rounded transition-colors"
                                                                title="Download"
                                                            >
                                                                ↓
                                                            </button>
                                                        </div>
                                                        <button
                                                            onClick={async () => {
                                                                if (confirm('Delete this image?')) {
                                                                    try {
                                                                        await notesApi.deleteAttachment(note.id, attachment.id);
                                                                        await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', noteId] });
                                                                    } catch (error) {
                                                                        console.error('Failed to delete image:', error);
                                                                    }
                                                                }
                                                            }}
                                                            className="absolute top-1 right-1 bg-red-500/90 text-white rounded w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                                                        >
                                                            ×
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Files List */}
                                    {note.attachments.filter(a => a.file_type !== 'image').length > 0 && (
                                        <div>
                                            <h4 className="text-[12px] text-gray-500 mb-2">Files</h4>
                                            <div className="space-y-2">
                                                {note.attachments.filter(a => a.file_type !== 'image').map((attachment) => (
                                                    <FileAttachment
                                                        key={attachment.id}
                                                        attachment={attachment}
                                                        showDelete={true}
                                                        onDelete={async () => {
                                                            if (confirm('Delete this file?')) {
                                                                try {
                                                                    await notesApi.deleteAttachment(note.id, attachment.id);
                                                                    await queryClient.invalidateQueries({ queryKey: ['notes', 'detail', noteId] });
                                                                } catch (error) {
                                                                    console.error('Failed to delete file:', error);
                                                                }
                                                            }
                                                        }}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}


                            {/* Action Buttons */}
                            <div className="flex items-center gap-3 border-t border-gray-700" style={{ marginTop: '0.5rem', paddingTop: '1rem' }}>
                                {!isCreating && (
                                    <>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="*/*"
                                            multiple
                                            onChange={handleImageUpload}
                                            className="hidden"
                                        />
                                        <button
                                            onClick={() => fileInputRef.current?.click()}
                                            disabled={isUploading}
                                            className="px-3 py-1.5 bg-[#2a2a2a] hover:bg-[#333] text-gray-300 text-[12px] border border-gray-700 rounded transition-colors disabled:opacity-50"
                                        >
                                            Upload Files
                                        </button>
                                    </>
                                )}
                                <button
                                    onClick={handleSave}
                                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-[12px] font-medium rounded transition-colors"
                                >
                                    {isCreating ? 'Create Note' : 'Save Changes'}
                                </button>
                                {isCreating && (
                                    <button
                                        onClick={onEditToggle}
                                        className="px-4 py-1.5 bg-gray-600 hover:bg-gray-500 text-white text-[12px] font-medium rounded transition-colors"
                                    >
                                        Cancel
                                    </button>
                                )}
                            </div>
                        </div>
                    ) : note ? (
                        /* View Mode */
                        <div>
                            {/* Title */}
                            <h1 className="text-2xl font-semibold text-white leading-tight" style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>{note.title}</h1>

                            {/* Metadata */}
                            <div className="flex items-center gap-6 text-[13px] text-gray-500 border-b border-gray-700" style={{ paddingBottom: '1rem', marginBottom: '0.75rem' }}>
                                <span>Created: {note.created_date && new Date(note.created_date).toLocaleDateString()}</span>
                                <span className="text-gray-700">|</span>
                                <span>Tags: {note.tags.length > 0 ? note.tags.map(t => `#${t}`).join(' ') : 'None'}</span>
                            </div>

                            {/* Content */}
                            <div className="py-4">
                                <RichTextEditor
                                    content={note.content}
                                    onChange={() => { }}
                                    editable={false}
                                />
                            </div>

                            {/* Attachments */}
                            {hasImages && (
                                <div className="border-t border-gray-700" style={{ marginTop: '1.5rem', paddingTop: '0.75rem' }}>
                                    <h3 className="text-[13px] font-medium text-gray-400 uppercase tracking-wider" style={{ marginBottom: '1.5rem' }}>Attachments</h3>

                                    {/* Images Grid */}
                                    {note.attachments.filter(a => a.file_type === 'image').length > 0 && (
                                        <div className="mb-4">
                                            <h4 className="text-[12px] text-gray-500 mb-2">Images</h4>
                                            <div className="grid grid-cols-3 gap-4">
                                                {note.attachments.filter(a => a.file_type === 'image').map((attachment) => (
                                                    <div key={attachment.id} className="relative group">
                                                        <img
                                                            src={`/uploads/${attachment.file_path}`}
                                                            alt=""
                                                            className="w-full h-44 object-cover rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                                            onClick={() => setShowGallery(true)}
                                                            onError={(e) => {
                                                                const target = e.target as HTMLImageElement;
                                                                target.style.display = 'none';
                                                                target.parentElement?.classList.add('bg-gray-700', 'flex', 'items-center', 'justify-center', 'h-44', 'rounded-lg');
                                                                const icon = document.createElement('span');
                                                                icon.textContent = '🖼️';
                                                                icon.className = 'text-4xl';
                                                                target.parentElement?.appendChild(icon);
                                                            }}
                                                        />
                                                        {/* Action buttons overlay */}
                                                        <div className="absolute bottom-2 left-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    window.open(`/uploads/${attachment.file_path}`, '_blank');
                                                                }}
                                                                className="flex-1 px-3 py-1.5 bg-blue-600/90 hover:bg-blue-500 text-white text-xs rounded transition-colors"
                                                                title="Open image"
                                                            >
                                                                Open
                                                            </button>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    const link = document.createElement('a');
                                                                    link.href = `/uploads/${attachment.file_path}`;
                                                                    link.download = attachment.original_filename || attachment.file_path;
                                                                    document.body.appendChild(link);
                                                                    link.click();
                                                                    document.body.removeChild(link);
                                                                }}
                                                                className="px-3 py-1.5 bg-gray-600/90 hover:bg-gray-500 text-white text-xs rounded transition-colors"
                                                                title="Download"
                                                            >
                                                                ↓
                                                            </button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Files List */}
                                    {note.attachments.filter(a => a.file_type !== 'image').length > 0 && (
                                        <div>
                                            <h4 className="text-[12px] text-gray-500 mb-2">Files</h4>
                                            <div className="space-y-2">
                                                {note.attachments.filter(a => a.file_type !== 'image').map((attachment) => (
                                                    <FileAttachment
                                                        key={attachment.id}
                                                        attachment={attachment}
                                                        showDelete={false}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </div>

            {/* Image Gallery Modal */}
            {showGallery && hasImages && note && (
                <ImageGallery
                    images={note.attachments}
                    onClose={() => setShowGallery(false)}
                />
            )}
        </div>
    );
}
