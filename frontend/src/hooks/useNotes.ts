import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notesApi } from '../api/notes';
import type { NoteCreate, NoteUpdate, NoteFilter } from '../types/note';

// Query keys
export const noteKeys = {
  all: ['notes'] as const,
  lists: () => [...noteKeys.all, 'list'] as const,
  list: (filters: NoteFilter) => [...noteKeys.lists(), filters] as const,
  details: () => [...noteKeys.all, 'detail'] as const,
  detail: (id: number) => [...noteKeys.details(), id] as const,
  tags: () => [...noteKeys.all, 'tags'] as const,
  categories: () => [...noteKeys.all, 'categories'] as const,
  stats: () => [...noteKeys.all, 'stats'] as const,
};

// List notes
export function useNotes(filters: NoteFilter = {}) {
  const query = useQuery({
    queryKey: noteKeys.list(filters),
    queryFn: () => notesApi.list(filters),
  });

  return {
    notes: query.data?.notes || [],
    total: query.data?.total || 0,
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

// Get single note
export function useNote(id: number | null) {
  return useQuery({
    queryKey: noteKeys.detail(id!),
    queryFn: () => notesApi.get(id!),
    enabled: id !== null,
  });
}

// Get tags
export function useTags() {
  return useQuery({
    queryKey: noteKeys.tags(),
    queryFn: () => notesApi.getTags(),
  });
}

// Get categories
export function useCategories() {
  return useQuery({
    queryKey: noteKeys.categories(),
    queryFn: () => notesApi.getCategories(),
  });
}

// Get stats
export function useNoteStats() {
  return useQuery({
    queryKey: noteKeys.stats(),
    queryFn: () => notesApi.getStats(),
  });
}

// Create note
export function useCreateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (note: NoteCreate) => notesApi.create(note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
      queryClient.invalidateQueries({ queryKey: noteKeys.tags() });
      queryClient.invalidateQueries({ queryKey: noteKeys.stats() });
    },
  });
}

// Update note
export function useUpdateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, note }: { id: number; note: NoteUpdate }) => notesApi.update(id, note),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: noteKeys.tags() });
    },
  });
}

// Delete note
export function useDeleteNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => notesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
      queryClient.invalidateQueries({ queryKey: noteKeys.stats() });
    },
  });
}

// Toggle pin
export function useTogglePin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, pin }: { id: number; pin: boolean }) => notesApi.togglePin(id, pin),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: noteKeys.stats() });
    },
  });
}

// Toggle archive
export function useToggleArchive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, archive }: { id: number; archive: boolean }) => notesApi.toggleArchive(id, archive),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: noteKeys.stats() });
    },
  });
}

// Upload attachment
export function useUploadAttachment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ noteId, file, filename }: { noteId: number; file: File | Blob; filename?: string }) =>
      notesApi.uploadAttachment(noteId, file, filename),
    onSuccess: (_, { noteId }) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(noteId) });
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
    },
  });
}

// Delete attachment
export function useDeleteAttachment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ noteId, attachmentId }: { noteId: number; attachmentId: number }) =>
      notesApi.deleteAttachment(noteId, attachmentId),
    onSuccess: (_, { noteId }) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(noteId) });
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() });
    },
  });
}
