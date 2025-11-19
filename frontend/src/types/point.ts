/**
 * Point types.
 */

export interface Tag {
  id: string;
  name: string;
}

export interface PointType {
  id: string;
  type: "base" | "custom";
  names: Record<string, string>; // Map of language_code to name
  creation_language: string;
  icon: string;
  order: number;
  owner: {
    id: string;
    email: string;
  } | null;
  visibility: "public" | "private";
  status: "active" | "deleted";
  created_at: string;
  updated_at: string;
}

export interface GPSPoint {
  id: string;
  title: string;
  description: string | null;
  latitude: number;
  longitude: number;
  is_public: boolean;
  owner: {
    id: string;
    email: string;
  };
  type?: PointType;
  tags: Tag[];
  annotation_count: number;
  created_at: string;
  updated_at: string;
  editing_lock_user: {
    id: string;
    email: string;
  } | null;
  editing_lock_acquired_at: string | null;
  shared_by: string | null; // Username of friend who shared this point
  share_count: number; // Number of users this point is shared with (owner only)
}

export interface CreatePointData {
  title: string;
  description?: string;
  latitude: number;
  longitude: number;
  type_id?: string;
  is_public?: boolean;
  tags?: string[];
}

export interface UpdatePointData {
  title?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  type_id?: string;
  is_public?: boolean;
  tags?: string[];
}

export interface CreatePointTypeData {
  names: Record<string, string>; // Map of language_code to name
  creation_language?: string;
  icon?: string;
  order?: number;
  visibility?: "public" | "private";
}

export interface UpdatePointTypeData {
  names?: Record<string, string>;
  icon?: string;
  order?: number;
  visibility?: "public" | "private";
}

export interface ReorderTypeData {
  id: string;
  order: number;
}

export interface PointsFilter {
  bbox?: {
    min_lon: number;
    min_lat: number;
    max_lon: number;
    max_lat: number;
  };
  tags?: string[];
  search?: string;
  is_public?: boolean;
}
