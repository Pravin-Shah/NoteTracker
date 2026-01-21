import { Search, Pin } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useNotes } from '../../hooks/useNotes';
import { formatDistanceToNow } from 'date-fns';
import type { Note } from '../../types/note';

export function FeedPane() {
  const {
    searchQuery,
    setSearchQuery,
    selectedNoteId,
    setSelectedNoteId,
    notesView,
    selectedTag,
    getFilter
  } = useAppStore();

  const filter = getFilter();
  const { notes, loading } = useNotes(filter);

  const getViewTitle = () => {
    if (selectedTag) return `#${selectedTag}`;
    switch (notesView) {
      case 'favorites': return 'Favorites';
      case 'trash': return 'Trash';
      default: return 'All Notes';
    }
  };

  return (
    <div className="w-[350px] min-w-[350px] h-full bg-[#252526] flex flex-col border-r border-gray-700">
      {/* Search Bar */}
      <div className="px-3 py-3 border-b border-gray-700">
        <div className="relative" style={{ paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"
          />
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#3c3c3c] border border-gray-600 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* View Title */}
      <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
        {getViewTitle()} ({notes.length})
      </div>

      {/* Notes List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-gray-500">Loading...</div>
        ) : notes.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {searchQuery ? 'No notes found' : 'No notes yet'}
          </div>
        ) : (
          notes.map((note: Note) => (
            <NoteCard
              key={note.id}
              note={note}
              isSelected={note.id === selectedNoteId}
              onClick={() => setSelectedNoteId(note.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface NoteCardProps {
  note: Note;
  isSelected: boolean;
  onClick: () => void;
}

function NoteCard({ note, isSelected, onClick }: NoteCardProps) {
  // Get preview text (first 100 chars of content)
  const preview = note.content
    .replace(/[#*`_\[\]]/g, '') // Remove markdown
    .slice(0, 100)
    .trim();

  // Format time
  const timeAgo = note.last_updated
    ? formatDistanceToNow(new Date(note.last_updated), { addSuffix: false })
      .replace('about ', '')
      .replace(' hours', 'h')
      .replace(' hour', 'h')
      .replace(' minutes', 'm')
      .replace(' minute', 'm')
      .replace(' days', 'd')
      .replace(' day', 'd')
    : '';

  // Check if note has image attachment
  const hasImage = note.attachments.some(
    (a) => a.file_type === 'image' || a.file_path.match(/\.(jpg|jpeg|png|gif)$/i)
  );
  const firstImage = hasImage
    ? note.attachments.find(
      (a) => a.file_type === 'image' || a.file_path.match(/\.(jpg|jpeg|png|gif)$/i)
    )
    : null;

  return (
    <button
      onClick={onClick}
      className={`w-full p-3 text-left border-b border-gray-700/50 transition-colors ${isSelected
        ? 'bg-[#37373d]'
        : 'hover:bg-[#2a2a2d]'
        }`}
    >
      <div className="flex gap-3">
        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title Row */}
          <div className="flex items-start gap-2">
            <h3 className="font-medium text-gray-200 truncate flex-1">
              {note.title}
            </h3>
            {note.pinned === 1 && (
              <Pin size={14} className="text-blue-400 flex-shrink-0 mt-0.5" />
            )}
          </div>

          {/* Preview */}
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {preview || 'No content'}
          </p>

          {/* Meta Row */}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-600">{timeAgo} ago</span>
            {note.tags.length > 0 && (
              <span className="text-xs text-gray-600">
                #{note.tags[0]}
                {note.tags.length > 1 && ` +${note.tags.length - 1}`}
              </span>
            )}
          </div>
        </div>

        {/* Thumbnail */}
        {firstImage && (
          <div className="w-14 h-14 flex-shrink-0 rounded overflow-hidden bg-gray-700">
            <img
              src={`/uploads/${firstImage.file_path.split('/').pop()}`}
              alt=""
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        )}
      </div>
    </button>
  );
}
