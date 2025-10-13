/**
 * Export/Import and Trash API calls.
 */

import { apiClient } from './client';

/**
 * Export format type.
 */
export type ExportFormat = 'geojson' | 'gpx' | 'kml' | 'csv' | 'zip';

/**
 * Import format type.
 */
export type ImportFormat = 'geojson' | 'gpx' | 'csv';

/**
 * Merge strategy for imports.
 */
export type MergeStrategy = 'create_new' | 'skip' | 'replace';

/**
 * Export request data.
 */
export interface ExportRequestData {
  point_ids?: string[];
  format: ExportFormat;
  include_annotations?: boolean;
}

/**
 * Import result.
 */
export interface ImportResult {
  total_points: number;
  imported_points: number;
  skipped_points: number;
  failed_points: number;
  errors: Array<{
    line_number: number;
    error: string;
    message: string;
  }>;
  created_point_ids: string[];
}

/**
 * Trash item.
 */
export interface TrashItem {
  id: string;
  gps_point: {
    id: string;
    title: string;
    latitude: number;
    longitude: number;
  };
  deleted_by: {
    id: string;
    email: string;
  };
  deleted_at: string;
  permanent_deletion_at: string;
}

/**
 * Export points.
 */
export async function exportPoints(data: ExportRequestData): Promise<Blob> {
  const response = await apiClient.post('/export/', data, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Import points from file.
 */
export async function importPoints(
  file: File,
  format: ImportFormat,
  mergeStrategy: MergeStrategy = 'create_new'
): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('format', format);
  formData.append('merge_strategy', mergeStrategy);

  const response = await apiClient.post<ImportResult>('/import/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Paginated response from API.
 */
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Get trash items.
 */
export async function getTrash(): Promise<TrashItem[]> {
  const response = await apiClient.get<PaginatedResponse<TrashItem>>('/trash/');
  return response.data.results;
}

/**
 * Restore point from trash.
 */
export async function restoreFromTrash(trashId: string): Promise<void> {
  await apiClient.post(`/trash/${trashId}/restore/`);
}

/**
 * Permanently delete point from trash.
 */
export async function permanentlyDelete(trashId: string): Promise<void> {
  await apiClient.delete(`/trash/${trashId}/permanent/`);
}

/**
 * Empty trash (delete all).
 */
export async function emptyTrash(): Promise<void> {
  await apiClient.delete('/trash/empty/');
}
