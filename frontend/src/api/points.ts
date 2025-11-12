/**
 * Points API calls.
 */

import { apiClient } from "./client";
import type {
  GPSPoint,
  CreatePointData,
  UpdatePointData,
  PointsFilter,
  Tag,
} from "../types/point";

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
 * Get all points with optional filters.
 */
export async function getPoints(filters?: PointsFilter): Promise<GPSPoint[]> {
  const params = new URLSearchParams();

  if (filters?.bbox) {
    params.append(
      "bbox",
      `${filters.bbox.min_lon},${filters.bbox.min_lat},${filters.bbox.max_lon},${filters.bbox.max_lat}`,
    );
  }

  if (filters?.tags && filters.tags.length > 0) {
    params.append("tags", filters.tags.join(","));
  }

  if (filters?.search) {
    params.append("search", filters.search);
  }

  if (filters?.is_public !== undefined) {
    params.append("is_public", filters.is_public.toString());
  }

  const response = await apiClient.get<PaginatedResponse<GPSPoint>>(
    `/points/?${params.toString()}`,
  );
  return response.data.results;
}

/**
 * Get point by ID.
 */
export async function getPoint(id: string): Promise<GPSPoint> {
  const response = await apiClient.get<GPSPoint>(`/points/${id}/`);
  return response.data;
}

/**
 * Create new point.
 */
export async function createPoint(data: CreatePointData): Promise<GPSPoint> {
  const response = await apiClient.post<GPSPoint>("/points/", data);
  return response.data;
}

/**
 * Update point.
 */
export async function updatePoint(
  id: string,
  data: UpdatePointData,
): Promise<GPSPoint> {
  const response = await apiClient.put<GPSPoint>(`/points/${id}/`, data);
  return response.data;
}

/**
 * Delete point (move to trash).
 */
export async function deletePoint(id: string): Promise<void> {
  await apiClient.delete(`/points/${id}/`);
}

/**
 * Acquire editing lock.
 */
export async function acquireLock(id: string): Promise<{
  locked_by: { id: string; email: string };
  acquired_at: string;
  expires_at: string;
}> {
  const response = await apiClient.post<{
    locked_by: { id: string; email: string };
    acquired_at: string;
    expires_at: string;
  }>(`/points/${id}/lock/`);
  return response.data;
}

/**
 * Release editing lock.
 */
export async function releaseLock(id: string): Promise<void> {
  await apiClient.delete(`/points/${id}/lock/`);
}

/**
 * Get all tags.
 */
export async function getTags(): Promise<Tag[]> {
  const response = await apiClient.get<Tag[]>("/tags/");
  return response.data;
}

/**
 * Search tags by name.
 */
export async function searchTags(query: string): Promise<Tag[]> {
  const response = await apiClient.get<Tag[]>(`/tags/?search=${query}`);
  return response.data;
}

/**
 * Create a new tag.
 */
export async function createTag(name: string): Promise<Tag> {
  const response = await apiClient.post<Tag>("/tags/", { name });
  return response.data;
}

/**
 * Update a tag.
 */
export async function updateTag(id: string, name: string): Promise<Tag> {
  const response = await apiClient.patch<Tag>(`/tags/${id}/`, { name });
  return response.data;
}

/**
 * Delete a tag.
 */
export async function deleteTag(id: string): Promise<void> {
  await apiClient.delete(`/tags/${id}/`);
}

/**
 * Search points by tags.
 */
export async function searchPointsByTags(
  tagNames: string[],
): Promise<GPSPoint[]> {
  const response = await apiClient.post<GPSPoint[]>("/points/search/tags/", {
    tags: tagNames,
  });
  return response.data;
}
