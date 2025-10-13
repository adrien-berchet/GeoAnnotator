/**
 * Annotation types.
 */

export interface FileMetadata {
  url: string;
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  can_preview: boolean;
}

export interface Annotation {
  id: string;
  gps_point_id: string;
  type: 'text' | 'image' | 'document' | 'file';
  text_content: string | null;
  file: FileMetadata | null;
  order: number;
  created_at: string;
  updated_at?: string;
  is_trashed: boolean;
  trash_days_remaining: number | null;
  trash_id: string | null;
}

export interface CreateTextAnnotationData {
  text_content: string;
}

export interface UpdateTextAnnotationData {
  text_content: string;
}
