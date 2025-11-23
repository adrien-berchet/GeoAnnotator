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
 * Paginated response from API (page number pagination).
 */
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Cursor paginated response from API.
 */
interface CursorPaginatedResponse<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Get points with cursor pagination (single page).
 * More efficient for large datasets, scales beyond 10k items.
 *
 * @param cursor - Cursor string from previous response (optional)
 * @param pageSize - Number of items per page (default: 100, max: 1000)
 * @param filters - Optional filters
 * @returns Paginated response with cursor for next page
 */
export async function getPointsPaginated(
  cursor?: string | null,
  pageSize: number = 100,
  filters?: PointsFilter,
): Promise<CursorPaginatedResponse<GPSPoint>> {
  const params = new URLSearchParams();

  if (cursor) {
    params.append("cursor", cursor);
  }

  params.append("page_size", Math.min(pageSize, 1000).toString());

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

  const response = await apiClient.get<CursorPaginatedResponse<GPSPoint>>(
    `/points/?${params.toString()}`,
  );

  return response.data;
}

/**
 * Get all points with optional filters.
 * Uses cursor pagination to fetch all results efficiently.
 * Automatically follows pagination cursors until all data is fetched.
 *
 * @param filters - Optional filters
 * @param onProgress - Optional callback for progress updates (current count, has more)
 * @returns Array of all points matching the filters
 */
export async function getPoints(
  filters?: PointsFilter,
  onProgress?: (count: number, hasMore: boolean) => void,
): Promise<GPSPoint[]> {
  const allPoints: GPSPoint[] = [];
  let cursor: string | null = null;
  let hasMore = true;

  // Fetch pages until no more results
  while (hasMore) {
    const response = await getPointsPaginated(cursor, 500, filters);

    allPoints.push(...response.results);

    cursor = response.next ? extractCursorFromUrl(response.next) : null;
    hasMore = cursor !== null;

    // Call progress callback if provided
    if (onProgress) {
      onProgress(allPoints.length, hasMore);
    }
  }

  return allPoints;
}

/**
 * Extract cursor parameter from pagination URL.
 */
function extractCursorFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url);
    return urlObj.searchParams.get("cursor");
  } catch {
    // If URL parsing fails, try to extract cursor from query string
    const match = url.match(/[?&]cursor=([^&]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }
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

/**
 * Batch update point type.
 */
export async function batchUpdatePointType(data: {
  point_ids: string[];
  type_id: string;
}): Promise<{
  success_count: number;
  error_count: number;
  skipped_count: number;
  total_attempted: number;
  results: Array<{ point_id: string; status: string; error?: string }>;
}> {
  const response = await apiClient.post("/points/batch/update-type/", data);
  return response.data;
}

/**
 * Batch add tags to points.
 */
export async function batchAddTags(data: {
  point_ids: string[];
  tags: string[];
}): Promise<{
  success_count: number;
  error_count: number;
  skipped_count: number;
  total_attempted: number;
  results: Array<{ point_id: string; status: string; error?: string }>;
}> {
  const response = await apiClient.post("/points/batch/add-tags/", data);
  return response.data;
}

/**
 * Batch delete/unshare points.
 * Owned points are deleted (moved to trash), shared points are unshared.
 */
export async function batchDeletePoints(data: {
  point_ids: string[];
}): Promise<{
  deleted_count: number;
  unshared_count: number;
  error_count: number;
  total_attempted: number;
  results: Array<{ point_id: string; status: string; error?: string }>;
}> {
  const response = await apiClient.post("/points/batch/delete/", data);
  return response.data;
}
