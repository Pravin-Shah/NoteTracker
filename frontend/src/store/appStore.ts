import { create } from 'zustand';
import type { NoteFilter } from '../types/note';

export type AppSection = 'notes' | 'tasks' | 'calendar' | 'tradevault';
export type NotesView = 'all' | 'favorites' | 'trash';

interface AppState {
  // Current section
  section: AppSection;
  setSection: (section: AppSection) => void;

  // Notes view
  notesView: NotesView;
  setNotesView: (view: NotesView) => void;

  // Selected note
  selectedNoteId: number | null;
  setSelectedNoteId: (id: number | null) => void;

  // Edit mode
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;

  // Creating new note
  isCreating: boolean;
  setIsCreating: (creating: boolean) => void;

  // Search query
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  // Selected tag filter
  selectedTag: string | null;
  setSelectedTag: (tag: string | null) => void;

  // Get current filter based on state
  getFilter: () => NoteFilter;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Section
  section: 'notes',
  setSection: (section) => set({ section, selectedNoteId: null, isEditing: false, isCreating: false }),

  // Notes view
  notesView: 'all',
  setNotesView: (notesView) => set({ notesView, selectedNoteId: null, isEditing: false, isCreating: false }),

  // Selected note
  selectedNoteId: null,
  setSelectedNoteId: (selectedNoteId) => set({ selectedNoteId, isEditing: false, isCreating: false }),

  // Edit mode
  isEditing: false,
  setIsEditing: (isEditing) => set({ isEditing }),

  // Creating
  isCreating: false,
  setIsCreating: (isCreating) => set({ isCreating, selectedNoteId: null, isEditing: false }),

  // Search
  searchQuery: '',
  setSearchQuery: (searchQuery) => set({ searchQuery }),

  // Tag filter
  selectedTag: null,
  setSelectedTag: (selectedTag) => set({ selectedTag }),

  // Build filter object
  getFilter: () => {
    const state = get();
    const filter: NoteFilter = {};

    if (state.searchQuery) {
      filter.query = state.searchQuery;
    }

    if (state.selectedTag) {
      filter.tag = state.selectedTag;
    }

    if (state.notesView === 'trash') {
      filter.archived = true;
    }

    if (state.notesView === 'favorites') {
      filter.pinned_only = true;
    }

    return filter;
  },
}));
