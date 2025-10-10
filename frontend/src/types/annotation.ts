/**
 * Annotation types.
 */

export interface Annotation {
  id: string;
  gps_point: string;
  type: 'text' | 'image' | 'document' | 'file';
  text_content: string | null;
  file: string | null;
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTextAnnotationData {
  text_content: string;
}

export interface UpdateTextAnnotationData {
  text_content: string;
}
