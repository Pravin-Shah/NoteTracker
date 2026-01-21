import {
  FileText,
  Star,
  Trash2,
  Plus,
  Calendar,
  CheckSquare,
  TrendingUp,
  Hash
} from 'lucide-react';
import { useAppStore, type AppSection, type NotesView } from '../../store/appStore';
import { useTags, useNoteStats } from '../../hooks/useNotes';

export function LeftPane() {
  const {
    section,
    setSection,
    notesView,
    setNotesView,
    setIsCreating,
    selectedTag,
    setSelectedTag
  } = useAppStore();

  const { data: tags = [] } = useTags();
  const { data: stats } = useNoteStats();

  const handleNewNote = () => {
    setSection('notes');
    setNotesView('all');
    setIsCreating(true);
  };

  const handleSectionChange = (newSection: AppSection) => {
    setSection(newSection);
    setSelectedTag(null);
  };

  const handleViewChange = (view: NotesView) => {
    setNotesView(view);
    setSelectedTag(null);
  };

  const handleTagClick = (tag: string) => {
    setSection('notes');
    setNotesView('all');
    setSelectedTag(tag === selectedTag ? null : tag);
  };

  return (
    <div className="w-[250px] min-w-[250px] h-full bg-[#1e1e1e] text-gray-200 flex flex-col border-r border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-semibold text-white">Notes</h1>
      </div>

      {/* New Note Button */}
      <div className="p-3">
        <button
          onClick={handleNewNote}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus size={18} />
          <span>New Note</span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto">
        {/* Notes Section */}
        <div className="px-2 py-1">
          <NavItem
            icon={<FileText size={18} />}
            label="All Notes"
            active={section === 'notes' && notesView === 'all' && !selectedTag}
            onClick={() => { handleSectionChange('notes'); handleViewChange('all'); }}
            count={stats?.active}
          />
          <NavItem
            icon={<Star size={18} />}
            label="Favorites"
            active={section === 'notes' && notesView === 'favorites'}
            onClick={() => { handleSectionChange('notes'); handleViewChange('favorites'); }}
            count={stats?.pinned}
          />
          <NavItem
            icon={<Trash2 size={18} />}
            label="Trash"
            active={section === 'notes' && notesView === 'trash'}
            onClick={() => { handleSectionChange('notes'); handleViewChange('trash'); }}
            count={stats?.archived}
          />
        </div>

        {/* Special Forms */}
        <div className="px-3 pt-4 pb-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Special Form
          </span>
        </div>
        <div className="px-2">
          <NavItem
            icon={<Calendar size={18} />}
            label="Daily Tracker"
            active={false}
            onClick={() => {}}
          />
          <NavItem
            icon={<CheckSquare size={18} />}
            label="Health Log"
            active={false}
            onClick={() => {}}
          />
        </div>

        {/* Tags Cloud */}
        <div className="px-3 pt-6 pb-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Tags Cloud
          </span>
        </div>
        <div className="px-3 pb-4">
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <button
                key={tag}
                onClick={() => handleTagClick(tag)}
                className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full transition-colors ${
                  selectedTag === tag
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <Hash size={10} />
                {tag}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Footer - App Sections */}
      <div className="border-t border-gray-700 p-2">
        <div className="flex gap-1">
          <SectionButton
            icon={<FileText size={16} />}
            label="Notes"
            active={section === 'notes'}
            onClick={() => handleSectionChange('notes')}
          />
          <SectionButton
            icon={<CheckSquare size={16} />}
            label="Tasks"
            active={section === 'tasks'}
            onClick={() => handleSectionChange('tasks')}
          />
          <SectionButton
            icon={<Calendar size={16} />}
            label="Calendar"
            active={section === 'calendar'}
            onClick={() => handleSectionChange('calendar')}
          />
          <SectionButton
            icon={<TrendingUp size={16} />}
            label="Trade"
            active={section === 'tradevault'}
            onClick={() => handleSectionChange('tradevault')}
          />
        </div>
      </div>
    </div>
  );
}

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  count?: number;
}

function NavItem({ icon, label, active, onClick, count }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
        active
          ? 'bg-gray-700 text-white'
          : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
      }`}
    >
      {icon}
      <span className="flex-1 text-left text-sm">{label}</span>
      {count !== undefined && count > 0 && (
        <span className="text-xs text-gray-500">{count}</span>
      )}
    </button>
  );
}

interface SectionButtonProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

function SectionButton({ icon, label, active, onClick }: SectionButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex flex-col items-center gap-0.5 py-1.5 rounded transition-colors ${
        active
          ? 'bg-gray-700 text-white'
          : 'text-gray-500 hover:bg-gray-800 hover:text-gray-300'
      }`}
      title={label}
    >
      {icon}
      <span className="text-[10px]">{label}</span>
    </button>
  );
}
