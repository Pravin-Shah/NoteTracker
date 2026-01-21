import { useState } from 'react';
import type { NoteCreate } from '../../types/note';
import { notesApi } from '../../api/notes';
import ImageUploader from './ImageUploader';

interface NoteFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

export default function NoteForm({ onSuccess, onCancel }: NoteFormProps) {
    const [formData, setFormData] = useState<NoteCreate>({
        title: '',
        content: '',
        category: null,
        importance: 3,
        color: null,
        tags: [],
    });
    const [tagInput, setTagInput] = useState('');
    const [uploadedImages, setUploadedImages] = useState<File[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            // Create the note first
            const note = await notesApi.create(formData);

            // Upload images if any
            if (uploadedImages.length > 0) {
                await Promise.all(
                    uploadedImages.map((file) => notesApi.uploadAttachment(note.id, file))
                );
            }

            onSuccess();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create note');
            setIsSubmitting(false);
        }
    };

    const handleAddTag = () => {
        const tag = tagInput.trim().toLowerCase();
        if (tag && !formData.tags?.includes(tag)) {
            setFormData({
                ...formData,
                tags: [...(formData.tags || []), tag],
            });
            setTagInput('');
        }
    };

    const handleRemoveTag = (tagToRemove: string) => {
        setFormData({
            ...formData,
            tags: formData.tags?.filter((tag) => tag !== tagToRemove) || [],
        });
    };

    const handleImagesChange = (files: File[]) => {
        setUploadedImages(files);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            )}

            {/* Title */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                </label>
                <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter note title"
                    required
                    minLength={3}
                    maxLength={100}
                />
            </div>

            {/* Category and Importance */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Category
                    </label>
                    <select
                        value={formData.category || ''}
                        onChange={(e) =>
                            setFormData({ ...formData, category: e.target.value || null })
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">Select category</option>
                        <option value="personal">Personal</option>
                        <option value="work">Work</option>
                        <option value="ideas">Ideas</option>
                        <option value="reference">Reference</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Importance: {'⭐'.repeat(formData.importance || 3)}
                    </label>
                    <input
                        type="range"
                        min="1"
                        max="5"
                        value={formData.importance || 3}
                        onChange={(e) =>
                            setFormData({ ...formData, importance: parseInt(e.target.value) })
                        }
                        className="w-full"
                    />
                </div>
            </div>

            {/* Content */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Content
                </label>
                <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={6}
                    placeholder="Enter note content"
                />
            </div>

            {/* Tags */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tags
                </label>
                <div className="flex gap-2 mb-2">
                    <input
                        type="text"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Add tag and press Enter"
                    />
                    <button
                        type="button"
                        onClick={handleAddTag}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                        Add
                    </button>
                </div>
                {formData.tags && formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {formData.tags.map((tag) => (
                            <span
                                key={tag}
                                className="inline-flex items-center gap-1 bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full"
                            >
                                #{tag}
                                <button
                                    type="button"
                                    onClick={() => handleRemoveTag(tag)}
                                    className="text-blue-600 hover:text-blue-800"
                                >
                                    ×
                                </button>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Image Uploader */}
            <ImageUploader onImagesChange={handleImagesChange} />

            {/* Actions */}
            <div className="flex gap-3 pt-4">
                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSubmitting ? 'Creating...' : '💾 Create Note'}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={isSubmitting}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50"
                >
                    Cancel
                </button>
            </div>
        </form>
    );
}
