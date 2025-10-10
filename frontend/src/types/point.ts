/**
 * Point types.
 */

export interface Tag {
  id: string;
  name: string;
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
  tags: Tag[];
  annotation_count: number;
  created_at: string;
  updated_at: string;
  editing_lock_user: {
    id: string;
    email: string;
  } | null;
  editing_lock_acquired_at: string | null;
}

export interface CreatePointData {
  title: string;
  description?: string;
  latitude: number;
  longitude: number;
  is_public?: boolean;
  tags?: string[];
}

export interface UpdatePointData {
  title?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  is_public?: boolean;
  tags?: string[];
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
