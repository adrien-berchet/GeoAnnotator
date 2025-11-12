/**
 * API client for trash operations.
 *
 * Handles soft-deleted points and annotations with 30-day retention.
 */

import { apiClient } from "./client";
import type { TrashPoint, TrashAnnotation, TrashStats } from "../types/trash";
import type { GPSPoint } from "../types/point";
import type { Annotation } from "../types/annotation";

/**
 * Point Trash API
 */

/**
 * Get all trashed points for current user.
 */
export async function getTrashPoints(): Promise<TrashPoint[]> {
  const response = await apiClient.get<TrashPoint[]>("/trash/points/");
  return response.data;
}

/**
 * Restore a point from trash.
 */
export async function restorePoint(pointId: string): Promise<GPSPoint> {
  const response = await apiClient.post<GPSPoint>(
    `/trash/points/${pointId}/restore/`,
  );
  return response.data;
}

/**
 * Permanently delete a point from trash.
 */
export async function permanentlyDeletePoint(pointId: string): Promise<void> {
  await apiClient.delete(`/trash/points/${pointId}/permanent/`);
}

/**
 * Empty all trashed points for current user.
 */
export async function emptyPointTrash(): Promise<{
  message: string;
  deleted_count: number;
}> {
  const response = await apiClient.delete<{
    message: string;
    deleted_count: number;
  }>("/trash/points/empty/");
  return response.data;
}

/**
 * Get trash statistics for points.
 */
export async function getPointTrashStats(): Promise<TrashStats> {
  const response = await apiClient.get<TrashStats>("/trash/points/stats/");
  return response.data;
}

/**
 * Annotation Trash API
 */

/**
 * Get all trashed annotations for current user's points.
 */
export async function getTrashAnnotations(): Promise<TrashAnnotation[]> {
  const response = await apiClient.get<TrashAnnotation[]>(
    "/trash/annotations/",
  );
  return response.data;
}

/**
 * Restore an annotation from trash.
 */
export async function restoreAnnotation(
  annotationId: string,
): Promise<Annotation> {
  const response = await apiClient.post<Annotation>(
    `/trash/annotations/${annotationId}/restore/`,
  );
  return response.data;
}

/**
 * Permanently delete an annotation from trash.
 */
export async function permanentlyDeleteAnnotation(
  annotationId: string,
): Promise<void> {
  await apiClient.delete(`/trash/annotations/${annotationId}/permanent/`);
}

/**
 * Empty all trashed annotations for current user.
 */
export async function emptyAnnotationTrash(): Promise<{
  message: string;
  deleted_count: number;
}> {
  const response = await apiClient.delete<{
    message: string;
    deleted_count: number;
  }>("/trash/annotations/empty/");
  return response.data;
}

/**
 * Get trash statistics for annotations.
 */
export async function getAnnotationTrashStats(): Promise<TrashStats> {
  const response = await apiClient.get<TrashStats>("/trash/annotations/stats/");
  return response.data;
}

/**
 * Combined operations
 */

/**
 * Get all trash data (points and annotations).
 */
export async function getAllTrashData() {
  const [points, annotations, pointsStats, annotationsStats] =
    await Promise.all([
      getTrashPoints(),
      getTrashAnnotations(),
      getPointTrashStats(),
      getAnnotationTrashStats(),
    ]);

  return {
    points,
    annotations,
    pointsStats,
    annotationsStats,
  };
}
