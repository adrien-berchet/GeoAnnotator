/**
 * Sharing API calls.
 */

import { apiClient } from "./client";

/**
 * Share types.
 */
export interface Share {
  id: string;
  gps_point: {
    id: string;
    title: string;
  };
  owner: {
    id: string;
    email: string;
    username?: string;
  };
  recipient_email: string;
  recipient_user: {
    id: string;
    email: string;
    username?: string;
  } | null;
  permission_level: "view" | "edit" | "manage";
  is_active: boolean;
  invitation_token: string;
  invitation_sent_at: string | null;
  accepted_at: string | null;
  created_at: string;
}

export interface CreateShareData {
  recipient_email: string;
  permission_level: "view" | "edit" | "manage";
}

export interface UpdateShareData {
  permission_level: "view" | "edit" | "manage";
}

/**
 * Get all shares for a point.
 */
export async function getPointShares(pointId: string): Promise<Share[]> {
  const response = await apiClient.get<Share[]>(`/points/${pointId}/sharing/`);
  return response.data;
}

/**
 * Create share for a point.
 */
export async function createShare(
  pointId: string,
  data: CreateShareData,
): Promise<Share> {
  const response = await apiClient.post<Share>(
    `/points/${pointId}/sharing/`,
    data,
  );
  return response.data;
}

/**
 * Get share by ID.
 */
export async function getShare(shareId: string): Promise<Share> {
  const response = await apiClient.get<Share>(`/sharing/${shareId}/`);
  return response.data;
}

/**
 * Update share permissions.
 */
export async function updateShare(
  shareId: string,
  data: UpdateShareData,
): Promise<Share> {
  const response = await apiClient.patch<Share>(`/sharing/${shareId}/`, data);
  return response.data;
}

/**
 * Delete (revoke) share.
 */
export async function deleteShare(shareId: string): Promise<void> {
  await apiClient.delete(`/sharing/${shareId}/`);
}

/**
 * Accept share invitation.
 */
export async function acceptShare(token: string): Promise<Share> {
  const response = await apiClient.post<Share>(`/sharing/accept/${token}/`);
  return response.data;
}

/**
 * Get received shares (shares where current user is recipient).
 */
export async function getReceivedShares(): Promise<Share[]> {
  const response = await apiClient.get<Share[]>("/sharing/received/");
  return response.data;
}
