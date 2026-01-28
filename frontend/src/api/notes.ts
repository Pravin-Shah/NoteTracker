import api from './client';
import type { Note, NoteCreate, NoteUpdate, NoteListResponse, NoteStats, NoteFilter, Attachment } from '../types/note';

export const notesApi = {
  // List notes with optional filters
  async list(filters: NoteFilter = {}): Promise<NoteListResponse> {
    const params = new URLSearchParams();
    if (filters.query) params.append('query', filters.query);
    if (filters.category) params.append('category', filters.category);
    if (filters.tag) params.append('tag', filters.tag);
    if (filters.importance) params.append('importance', filters.importance.toString());
    if (filters.archived !== undefined) params.append('archived', filters.archived.toString());
    if (filters.pinned_only) params.append('pinned_only', 'true');

    const response = await api.get<NoteListResponse>(`/api/notes?${params.toString()}`);
    return response.data;
  },

  // Get single note by ID
  async get(id: number): Promise<Note> {
    const response = await api.get<Note>(`/api/notes/${id}`);
    return response.data;
  },

  // Create new note
  async create(note: NoteCreate): Promise<Note> {
    const response = await api.post<Note>('/api/notes', note);
    return response.data;
  },

  // Update existing note
  async update(id: number, note: NoteUpdate): Promise<Note> {
    const response = await api.put<Note>(`/api/notes/${id}`, note);
    return response.data;
  },

  // Delete (archive) note
  async delete(id: number): Promise<void> {
    await api.delete(`/api/notes/${id}`);
  },

  // Permanently delete note
  async permanentDelete(id: number): Promise<void> {
    await api.delete(`/api/notes/${id}/permanent`);
  },

  // Pin/unpin note
  async togglePin(id: number, pin: boolean): Promise<Note> {
    const response = await api.post<Note>(`/api/notes/${id}/pin?pin=${pin}`);
    return response.data;
  },

  // Archive/restore note
  async toggleArchive(id: number, archive: boolean): Promise<Note> {
    const response = await api.post<Note>(`/api/notes/${id}/archive?archive=${archive}`);
    return response.data;
  },

  // Get all tags
  async getTags(): Promise<string[]> {
    const response = await api.get<{ tags: string[] }>('/api/notes/tags');
    return response.data.tags;
  },

  // Get all categories
  async getCategories(): Promise<string[]> {
    const response = await api.get<{ categories: string[] }>('/api/notes/categories');
    return response.data.categories;
  },

  // Get note statistics
  async getStats(): Promise<NoteStats> {
    const response = await api.get<NoteStats>('/api/notes/stats');
    return response.data;
  },

  // Upload attachment (image/file)
  async uploadAttachment(noteId: number, file: File | Blob, filename?: string): Promise<Attachment> {
    const formData = new FormData();

    // Determine the actual filename to use
    let actualFilename: string;
    if (filename) {
      actualFilename = filename;
    } else if (file instanceof File) {
      // Use the actual filename from the File object
      actualFilename = file.name;
    } else {
      // For Blob objects (e.g., pasted images), generate a name based on type
      const ext = file.type.split('/')[1] || 'png';
      actualFilename = `pasted_${Date.now()}.${ext}`;
    }

    formData.append('file', file, actualFilename);

    const response = await api.post<Attachment>(
      `/api/notes/${noteId}/attachments`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Delete attachment
  async deleteAttachment(noteId: number, attachmentId: number): Promise<void> {
    await api.delete(`/api/notes/${noteId}/attachments/${attachmentId}`);
  },
};
