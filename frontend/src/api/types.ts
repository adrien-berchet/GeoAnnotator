/**
 * Point Types API calls.
 */

import { apiClient } from "./client";
import type {
  PointType,
  CreatePointTypeData,
  UpdatePointTypeData,
  ReorderTypeData,
} from "../types/point";

/**
 * Get all point types for the current user.
 * Includes user's own types and base types (user=null).
 */
export async function getPointTypes(): Promise<PointType[]> {
  const response = await apiClient.get<PointType[]>("/types/");

  // Ensure we return an array
  if (Array.isArray(response.data)) {
    return response.data;
  }

  // If data is wrapped in a results property (pagination)
  if (
    response.data &&
    typeof response.data === "object" &&
    "results" in response.data
  ) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (response.data as any).results;
  }

  console.error("Unexpected response format from /types/:", response.data);
  return [];
}

/**
 * Get point type by ID.
 */
export async function getPointType(id: string): Promise<PointType> {
  const response = await apiClient.get<PointType>(`/types/${id}/`);
  return response.data;
}

/**
 * Create new point type.
 */
export async function createPointType(
  data: CreatePointTypeData,
): Promise<PointType> {
  const response = await apiClient.post<PointType>("/types/", data);
  return response.data;
}

/**
 * Update point type.
 */
export async function updatePointType(
  id: string,
  data: UpdatePointTypeData,
): Promise<PointType> {
  const response = await apiClient.patch<PointType>(`/types/${id}/`, data);
  return response.data;
}

/**
 * Delete point type (soft delete).
 * Associated points will be switched to the default 'Point' type.
 */
export async function deletePointType(id: string): Promise<void> {
  await apiClient.delete(`/types/${id}/`);
}

/**
 * Reorder point types.
 * Updates the display order for multiple types at once.
 */
export async function reorderPointTypes(
  order: ReorderTypeData[],
): Promise<{ success: boolean; updated: number }> {
  const response = await apiClient.post<{ success: boolean; updated: number }>(
    "/types/reorder/",
    { order },
  );
  return response.data;
}

/**
 * Upload an icon file for a point type.
 * Supports SVG, PNG, JPG, JPEG files (max 1MB).
 */
export async function uploadTypeIcon(
  file: File,
): Promise<{ icon_url: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<{ icon_url: string }>(
    "/types/upload-icon/",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

/**
 * Download an icon from external URL and save it.
 * The backend will fetch the URL and store it locally.
 */
export async function downloadTypeIcon(
  url: string,
): Promise<{ icon_url: string }> {
  const response = await apiClient.post<{ icon_url: string }>(
    "/types/upload-icon/",
    {
      url: url,
    },
  );

  return response.data;
}
