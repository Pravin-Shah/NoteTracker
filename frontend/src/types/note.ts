export interface Attachment {
  id: number;
  file_path: string;
  file_type: string | null;
  original_filename?: string | null;
  file_size?: number | null;
  upload_date: string | null;
}

export interface Note {
  id: number;
  user_id: number;
  title: string;
  content: string;
  category: string | null;
  importance: number;
  color: string | null;
  created_date: string | null;
  last_updated: string | null;
  archived: number;
  pinned: number;
  tags: string[];
  attachments: Attachment[];
}

export interface NoteCreate {
  title: string;
  content: string;
  category?: string | null;
  importance?: number;
  color?: string | null;
  tags?: string[];
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  category?: string | null;
  importance?: number;
  color?: string | null;
  tags?: string[];
}

export interface NoteListResponse {
  notes: Note[];
  total: number;
}

export interface NoteStats {
  total: number;
  pinned: number;
  archived: number;
  active: number;
  by_category: Record<string, number>;
}

export interface NoteFilter {
  query?: string;
  category?: string;
  tag?: string;
  importance?: number;
  archived?: boolean;
  pinned_only?: boolean;
}
