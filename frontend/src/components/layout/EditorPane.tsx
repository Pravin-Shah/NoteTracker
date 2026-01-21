import { useState, useEffect, useRef, useCallback } from 'react';
import { Edit, Trash2, Pin, RotateCcw, ChevronRight, X, Save, Upload, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAppStore } from '../../store/appStore';
import {
  useNote,
  useCreateNote,
  useUpdateNote,
  useDeleteNote,
  useTogglePin,
  useToggleArchive,
  useTags,
  useCategories,
  useUploadAttachment,
  useDeleteAttachment
} from '../../hooks/useNotes';
import { format } from 'date-fns';
import type { NoteCreate, NoteUpdate, Attachment } from '../../types/note';

export function EditorPane() {
  const {
    selectedNoteId,
    setSelectedNoteId,
    isEditing,
    setIsEditing,
    isCreating,
    setIsCreating,
    notesView
  } = useAppStore();

  const { data: note } = useNote(selectedNoteId);
  const { data: allTags = [] } = useTags();
  const { data: allCategories = [] } = useCategories();

  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();
  const togglePin = useTogglePin();
  const toggleArchive = useToggleArchive();
  const uploadAttachment = useUploadAttachment();
  const deleteAttachment = useDeleteAttachment();

  // Form state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [importance, setImportance] = useState(3);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  // Pending images for new notes (before save)
  const [pendingImages, setPendingImages] = useState<{ blob: Blob; preview: string }[]>([]);

  // Reset form when switching notes or modes
  useEffect(() => {
    if (isCreating) {
      setTitle('');
      setContent('');
      setCategory('');
      setImportance(3);
      setTags([]);
      setPendingImages([]);
    } else if (note && isEditing) {
      setTitle(note.title);
      setContent(note.content);
      setCategory(note.category || '');
      setImportance(note.importance);
      setTags(note.tags);
      setPendingImages([]);
    }
  }, [isCreating, isEditing, note]);

  // Cleanup pending image previews
  useEffect(() => {
    return () => {
      pendingImages.forEach((img) => URL.revokeObjectURL(img.preview));
    };
  }, [pendingImages]);

  const handleSave = async () => {
    if (isCreating) {
      const newNote: NoteCreate = {
        title: title.trim() || 'Untitled',
        content,
        category: category || undefined,
        importance,
        tags,
      };
      const created = await createNote.mutateAsync(newNote);

      // Upload pending images
      for (const img of pendingImages) {
        await uploadAttachment.mutateAsync({
          noteId: created.id,
          file: img.blob,
          filename: `pasted-${Date.now()}.png`
        });
      }

      setPendingImages([]);
      setIsCreating(false);
      setSelectedNoteId(created.id);
    } else if (note && isEditing) {
      const updates: NoteUpdate = {
        title: title.trim() || note.title,
        content,
        category: category || null,
        importance,
        tags,
      };
      await updateNote.mutateAsync({ id: note.id, note: updates });
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    pendingImages.forEach((img) => URL.revokeObjectURL(img.preview));
    setPendingImages([]);
    if (isCreating) {
      setIsCreating(false);
    } else {
      setIsEditing(false);
    }
  };

  const handleAddTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
    }
    setTagInput('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleDelete = async () => {
    if (note && window.confirm('Move this note to trash?')) {
      await deleteNote.mutateAsync(note.id);
      setSelectedNoteId(null);
    }
  };

  const handlePin = async () => {
    if (note) {
      await togglePin.mutateAsync({ id: note.id, pin: note.pinned !== 1 });
    }
  };

  const handleRestore = async () => {
    if (note) {
      await toggleArchive.mutateAsync({ id: note.id, archive: false });
    }
  };

  // Handle image paste for existing notes (in edit mode)
  const handleImagePaste = useCallback(async (blob: Blob) => {
    if (note && isEditing) {
      // Upload immediately for existing notes
      await uploadAttachment.mutateAsync({
        noteId: note.id,
        file: blob,
        filename: `pasted-${Date.now()}.png`
      });
    } else if (isCreating) {
      // Store for later upload (after note is created)
      const preview = URL.createObjectURL(blob);
      setPendingImages((prev) => [...prev, { blob, preview }]);
    }
  }, [note, isEditing, isCreating, uploadAttachment]);

  const handleRemovePendingImage = (index: number) => {
    setPendingImages((prev) => {
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleDeleteAttachment = async (attachmentId: number) => {
    if (note && window.confirm('Delete this image?')) {
      await deleteAttachment.mutateAsync({
        noteId: note.id,
        attachmentId
      });
    }
  };

  // Show create form
  if (isCreating) {
    return (
      <div className="flex-1 h-full bg-white flex flex-col overflow-hidden">
        <EditorHeader
          title="New Note"
          onSave={handleSave}
          onCancel={handleCancel}
          isSaving={createNote.isPending || uploadAttachment.isPending}
        />
        <EditorForm
          title={title}
          setTitle={setTitle}
          content={content}
          setContent={setContent}
          category={category}
          setCategory={setCategory}
          importance={importance}
          setImportance={setImportance}
          tags={tags}
          tagInput={tagInput}
          setTagInput={setTagInput}
          onAddTag={handleAddTag}
          onRemoveTag={handleRemoveTag}
          allTags={allTags}
          allCategories={allCategories}
          onImagePaste={handleImagePaste}
          pendingImages={pendingImages}
          onRemovePendingImage={handleRemovePendingImage}
          isUploading={uploadAttachment.isPending}
        />
      </div>
    );
  }

  // Show edit form
  if (isEditing && note) {
    return (
      <div className="flex-1 h-full bg-white flex flex-col overflow-hidden">
        <EditorHeader
          title="Edit Note"
          onSave={handleSave}
          onCancel={handleCancel}
          isSaving={updateNote.isPending}
        />
        <EditorForm
          title={title}
          setTitle={setTitle}
          content={content}
          setContent={setContent}
          category={category}
          setCategory={setCategory}
          importance={importance}
          setImportance={setImportance}
          tags={tags}
          tagInput={tagInput}
          setTagInput={setTagInput}
          onAddTag={handleAddTag}
          onRemoveTag={handleRemoveTag}
          allTags={allTags}
          allCategories={allCategories}
          onImagePaste={handleImagePaste}
          existingAttachments={note.attachments}
          onDeleteAttachment={handleDeleteAttachment}
          isUploading={uploadAttachment.isPending}
        />
      </div>
    );
  }

  // Show note viewer
  if (selectedNoteId && note) {
    return (
      <div className="flex-1 h-full bg-white flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200">
          <Breadcrumb items={['All Notes', note.title]} />
          <div className="flex items-center gap-2">
            {notesView === 'trash' ? (
              <button
                onClick={handleRestore}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              >
                <RotateCcw size={16} />
                Restore
              </button>
            ) : (
              <>
                <button
                  onClick={handlePin}
                  className={`p-2 rounded-lg transition-colors ${note.pinned === 1
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-400 hover:bg-gray-100'
                    }`}
                  title={note.pinned === 1 ? 'Unpin' : 'Pin'}
                >
                  <Pin size={18} />
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Edit size={16} />
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Delete"
                >
                  <Trash2 size={18} />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{note.title}</h1>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-6">
            <span>
              Created: {note.created_date ? format(new Date(note.created_date), 'MMM d, yyyy') : 'Unknown'}
            </span>
            {note.category && (
              <>
                <span className="text-gray-300">•</span>
                <span className="capitalize">{note.category}</span>
              </>
            )}
            {note.tags.length > 0 && (
              <>
                <span className="text-gray-300">•</span>
                <span>Tags: {note.tags.map((t) => `#${t}`).join(' ')}</span>
              </>
            )}
          </div>

          {/* Content with Markdown */}
          <div className="markdown-content prose prose-gray max-w-none">
            <MarkdownWithWikiLinks content={note.content} />
          </div>

          {/* Embedded Images - Show all images inline */}
          {note.attachments.length > 0 && (
            <div className="mt-8 space-y-4">
              {note.attachments
                .filter((a) => a.file_type === 'image' || a.file_path.match(/\.(jpg|jpeg|png|gif|webp)$/i))
                .map((attachment) => (
                  <div key={attachment.id} className="rounded-lg overflow-hidden border border-gray-200">
                    <img
                      src={`/uploads/${attachment.file_path}`}
                      alt=""
                      className="max-w-full h-auto"
                      loading="lazy"
                    />
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Empty state
  return (
    <div className="flex-1 h-full bg-white flex items-center justify-center">
      <div className="text-center text-gray-400">
        <p className="text-lg">Select a note to view</p>
        <p className="text-sm mt-1">or create a new one</p>
      </div>
    </div>
  );
}

// Helper Components

function Breadcrumb({ items }: { items: string[] }) {
  return (
    <div className="flex items-center gap-1 text-sm text-gray-500">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight size={14} className="text-gray-300" />}
          <span className={i === items.length - 1 ? 'text-gray-900 font-medium' : ''}>
            {item}
          </span>
        </span>
      ))}
    </div>
  );
}

function EditorHeader({
  title,
  onSave,
  onCancel,
  isSaving
}: {
  title: string;
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200">
      <span className="font-medium text-gray-900">{title}</span>
      <div className="flex items-center gap-2">
        <button
          onClick={onCancel}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <X size={16} />
          Cancel
        </button>
        <button
          onClick={onSave}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  );
}

interface EditorFormProps {
  title: string;
  setTitle: (v: string) => void;
  content: string;
  setContent: (v: string) => void;
  category: string;
  setCategory: (v: string) => void;
  importance: number;
  setImportance: (v: number) => void;
  tags: string[];
  tagInput: string;
  setTagInput: (v: string) => void;
  onAddTag: () => void;
  onRemoveTag: (tag: string) => void;
  allTags: string[];
  allCategories: string[];
  onImagePaste: (blob: Blob) => void;
  pendingImages?: { blob: Blob; preview: string }[];
  onRemovePendingImage?: (index: number) => void;
  existingAttachments?: Attachment[];
  onDeleteAttachment?: (id: number) => void;
  isUploading?: boolean;
}

function EditorForm({
  title,
  setTitle,
  content,
  setContent,
  category,
  setCategory,
  importance,
  setImportance,
  tags,
  tagInput,
  setTagInput,
  onAddTag,
  onRemoveTag,
  allTags,
  allCategories,
  onImagePaste,
  pendingImages = [],
  onRemovePendingImage,
  existingAttachments = [],
  onDeleteAttachment,
  isUploading = false
}: EditorFormProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle paste event
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const blob = item.getAsFile();
          if (blob) {
            onImagePaste(blob);
          }
          break;
        }
      }
    };

    const textarea = textareaRef.current;
    if (textarea) {
      textarea.addEventListener('paste', handlePaste);
      return () => textarea.removeEventListener('paste', handlePaste);
    }
  }, [onImagePaste]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        onImagePaste(file);
      }
    }
    e.target.value = '';
  };

  const imageAttachments = existingAttachments.filter(
    (a) => a.file_type === 'image' || a.file_path.match(/\.(jpg|jpeg|png|gif|webp)$/i)
  );

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {/* Title */}
      <input
        type="text"
        placeholder="Note title..."
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full text-2xl font-bold text-gray-900 placeholder-gray-400 border-0 outline-none mb-4"
        autoFocus
      />

      {/* Meta Row */}
      <div className="flex flex-wrap gap-4 mb-6 pb-4 border-b border-gray-200">
        {/* Category */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">Category:</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 outline-none focus:border-blue-500"
          >
            <option value="">None</option>
            <option value="personal">Personal</option>
            <option value="work">Work</option>
            <option value="financial">Financial</option>
            <option value="health">Health</option>
            <option value="ideas">Ideas</option>
            {allCategories
              .filter((c) => !['personal', 'work', 'financial', 'health', 'ideas'].includes(c))
              .map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
          </select>
        </div>

        {/* Importance */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">Importance:</label>
          <select
            value={importance}
            onChange={(e) => setImportance(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded px-2 py-1 outline-none focus:border-blue-500"
          >
            <option value={1}>1 - Low</option>
            <option value={2}>2</option>
            <option value={3}>3 - Medium</option>
            <option value={4}>4</option>
            <option value={5}>5 - High</option>
          </select>
        </div>
      </div>

      {/* Tags */}
      <div className="mb-6">
        <label className="block text-sm text-gray-500 mb-2">Tags:</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-sm rounded-full"
            >
              #{tag}
              <button
                onClick={() => onRemoveTag(tag)}
                className="hover:text-blue-900"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Add tag..."
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), onAddTag())}
            list="tag-suggestions"
            className="flex-1 text-sm border border-gray-300 rounded px-3 py-1.5 outline-none focus:border-blue-500"
          />
          <datalist id="tag-suggestions">
            {allTags.filter((t) => !tags.includes(t)).map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
          <button
            onClick={onAddTag}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            Add
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm text-gray-500">Content (Markdown):</label>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
          >
            <Upload size={14} />
            Add Image
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
        <textarea
          ref={textareaRef}
          placeholder="Write your note here... Use Markdown for formatting. Paste images with Ctrl+V."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full h-[300px] text-gray-900 border border-gray-300 rounded-lg p-4 outline-none focus:border-blue-500 resize-none font-mono text-sm"
        />
      </div>

      {/* Images Section */}
      {(pendingImages.length > 0 || imageAttachments.length > 0) && (
        <div className="mb-6">
          <label className="block text-sm text-gray-500 mb-2">
            Images ({pendingImages.length + imageAttachments.length})
            {isUploading && <Loader2 size={14} className="inline ml-2 animate-spin" />}
          </label>
          <div className="grid grid-cols-3 gap-3">
            {/* Existing attachments */}
            {imageAttachments.map((attachment) => (
              <div key={attachment.id} className="relative group">
                <img
                  src={`/uploads/${attachment.file_path}`}
                  alt=""
                  className="w-full h-32 object-cover rounded-lg border border-gray-200"
                />
                {onDeleteAttachment && (
                  <button
                    onClick={() => onDeleteAttachment(attachment.id)}
                    className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            ))}
            {/* Pending images */}
            {pendingImages.map((img, index) => (
              <div key={index} className="relative group">
                <img
                  src={img.preview}
                  alt=""
                  className="w-full h-32 object-cover rounded-lg border border-blue-300 border-dashed"
                />
                <div className="absolute inset-0 bg-blue-500/10 rounded-lg flex items-center justify-center">
                  <span className="text-xs text-blue-600 bg-white px-2 py-0.5 rounded">Pending</span>
                </div>
                {onRemovePendingImage && (
                  <button
                    onClick={() => onRemovePendingImage(index)}
                    className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remove"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Paste images with Ctrl+V or click "Add Image"
          </p>
        </div>
      )}
    </div>
  );
}

// Markdown with wiki-links
function MarkdownWithWikiLinks({ content }: { content: string }) {
  // Replace [[wiki-links]] with clickable spans
  const processedContent = content.replace(
    /\[\[([^\]]+)\]\]/g,
    (_, linkText) => `<span class="wiki-link" data-link="${linkText}">${linkText}</span>`
  );

  return (
    <ReactMarkdown
      components={{
        // Handle raw HTML for wiki-links
        p: ({ children, ...props }) => {
          // Check if children contains our wiki-link spans
          if (typeof children === 'string' && children.includes('wiki-link')) {
            return <p {...props} dangerouslySetInnerHTML={{ __html: children }} />;
          }
          return <p {...props}>{children}</p>;
        }
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );
}
