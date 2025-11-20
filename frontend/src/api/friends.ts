/**
 * Friends API client
 *
 * Handles friendship management endpoints
 */

import { apiClient } from "./client";

/**
 * Friend interface with share statistics
 * Note: Email is excluded for privacy
 */
export interface Friend {
  id: string;
  friendship_id: string;
  username: string;
  shares_sent_count: number;
  shares_received_count: number;
  friendship_created_at: string;
}

/**
 * Friendship interface
 */
export interface Friendship {
  id: string;
  friend: {
    id: string;
  };
  created_at: string;
}

/**
 * Friend detail with shared points
 * Note: Email is excluded for privacy
 */
export interface FriendDetail {
  id: string;
  username: string;
  friendship_created_at: string;
  shared_points: Array<{
    id: string;
    title: string;
    latitude: number;
    longitude: number;
    type?: {
      id: string;
      names: Record<string, string>;
      icon: string;
    };
    tags: Array<{
      id: string;
      name: string;
    }>;
    created_at: string;
    share_id: string;
    permission_level: "view" | "edit" | "transfer";
  }>;
  shares_sent_count: number;
  shares_received_count: number;
}

/**
 * Add friend request
 */
export interface AddFriendRequest {
  username: string;
}

/**
 * Remove friend response
 */
export interface RemoveFriendResponse {
  message: string;
  friendships_deleted: number;
  shares_revoked: number;
  details: {
    shares_revoked_to_friend: number;
    shares_revoked_from_friend: number;
  };
}

/**
 * Get list of friends with share statistics
 */
export async function getFriends(): Promise<Friend[]> {
  const response = await apiClient.get<Friend[]>("/sharing/friendships/");
  return response.data;
}

/**
 * Add a friend by username
 */
export async function addFriend(username: string): Promise<Friendship> {
  const response = await apiClient.post<Friendship>("/sharing/friendships/", {
    username,
  });
  return response.data;
}

/**
 * Get friend detail with shared points
 */
export async function getFriendDetail(friendshipId: string): Promise<FriendDetail> {
  const response = await apiClient.get<FriendDetail>(
    `/sharing/friendships/${friendshipId}/`
  );
  return response.data;
}

/**
 * Remove a friend and revoke all shares
 */
export async function removeFriend(
  friendshipId: string
): Promise<RemoveFriendResponse> {
  const response = await apiClient.delete<RemoveFriendResponse>(
    `/sharing/friendships/${friendshipId}/`
  );
  return response.data;
}

/**
 * Batch share points with multiple users
 */
export interface BatchShareRequest {
  point_ids: string[];
  usernames: string[];
  permission_level: "view" | "edit" | "transfer";
}

export interface BatchShareResult {
  point_id: string;
  username: string;
  status: "success" | "error" | "already_shared";
  error?: string;
  message?: string;
  share_id?: string;
}

export interface BatchShareResponse {
  success_count: number;
  error_count: number;
  already_shared_count: number;
  total_attempted: number;
  results: BatchShareResult[];
}

/**
 * Share multiple points with multiple users
 */
export async function batchSharePoints(
  request: BatchShareRequest
): Promise<BatchShareResponse> {
  const response = await apiClient.post<BatchShareResponse>(
    "/sharing/batch/",
    request
  );
  return response.data;
}
