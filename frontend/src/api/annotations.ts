/**
 * Annotations API calls.
 */

import { apiClient } from './client';
import type { Annotation, CreateTextAnnotationData, UpdateTextAnnotationData } from '../types/annotation';

/**
 * Get all annotations for a point.
 */
export async function getAnnotations(pointId: string): Promise<Annotation[]> {
  const response = await apiClient.get<Annotation[]>(`/points/${pointId}/annotations/`);
  return response.data;
}

/**
 * Get annotation by ID.
 */
export async function getAnnotation(pointId: string, annotationId: string): Promise<Annotation> {
  const response = await apiClient.get<Annotation>(`/points/${pointId}/annotations/${annotationId}/`);
  return response.data;
}

/**
 * Create text annotation.
 */
export async function createTextAnnotation(
  pointId: string,
  data: CreateTextAnnotationData
): Promise<Annotation> {
  const response = await apiClient.post<Annotation>(`/points/${pointId}/annotations/`, {
    type: 'text',
    ...data,
  });
  return response.data;
}

/**
 * Create file annotation (image, document, or file).
 */
export async function createFileAnnotation(
  pointId: string,
  file: File,
  type: 'image' | 'document' | 'file'
): Promise<Annotation> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);

  const response = await apiClient.post<Annotation>(`/points/${pointId}/annotations/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Update text annotation.
 */
export async function updateTextAnnotation(
  pointId: string,
  annotationId: string,
  data: UpdateTextAnnotationData
): Promise<Annotation> {
  const response = await apiClient.put<Annotation>(
    `/points/${pointId}/annotations/${annotationId}/`,
    data
  );
  return response.data;
}

/**
 * Delete annotation.
 */
export async function deleteAnnotation(pointId: string, annotationId: string): Promise<void> {
  await apiClient.delete(`/points/${pointId}/annotations/${annotationId}/`);
}

/**
 * Download annotation file.
 */
export async function downloadAnnotation(pointId: string, annotationId: string): Promise<Blob> {
  const response = await apiClient.get(`/points/${pointId}/annotations/${annotationId}/download/`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Get annotation preview URL.
 */
export function getPreviewUrl(annotationId: string): string {
  return `${apiClient.defaults.baseURL}/annotations/${annotationId}/preview/`;
}

/**
 * Reorder annotations for a point.
 */
export async function reorderAnnotations(
  pointId: string,
  annotations: Array<{ id: string; order: number }>
): Promise<void> {
  await apiClient.post(`/points/${pointId}/annotations/reorder/`, {
    annotations,
  });
}
