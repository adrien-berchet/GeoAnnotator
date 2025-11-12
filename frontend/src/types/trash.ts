/**
 * Trash types for soft-deleted points and annotations.
 */

import type { GPSPoint } from "./point";
import type { Annotation } from "./annotation";

export interface User {
  id: string;
  email: string;
}

export interface Share {
  id: string;
  recipient_email: string;
  permission: "view" | "edit" | "transfer";
  status: "pending" | "accepted";
  is_active: boolean;
  created_at: string;
}

/**
 * Point trash item with annotations and shares.
 */
export interface TrashPoint {
  id: string;
  gps_point: GPSPoint;
  deleted_by: User;
  deleted_at: string;
  permanent_deletion_at: string;
  days_remaining: number;
  is_expired: boolean;
  annotations: Annotation[];
  shares: Share[];
}

/**
 * Annotation trash item with associated point.
 */
export interface TrashAnnotation {
  id: string;
  annotation: Annotation;
  gps_point: GPSPoint;
  deleted_by: User;
  deleted_at: string;
  permanent_deletion_at: string;
  days_remaining: number;
  is_expired: boolean;
}

/**
 * Trash statistics.
 */
export interface TrashStats {
  total_items: number;
  expiring_soon: number;
  oldest_item_age_days: number;
}

/**
 * Combined trash data for the UI.
 */
export interface TrashData {
  points: TrashPoint[];
  annotations: TrashAnnotation[];
  pointsStats: TrashStats;
  annotationsStats: TrashStats;
}
