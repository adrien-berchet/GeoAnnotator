/**
 * Point types.
 */

export interface Tag {
  id: string;
  name: string;
}

export interface PointType {
  id: string;
  name: string;
  icon: string;
  order: number;
  user: {
    id: string;
    email: string;
  } | null;
  status: 'active' | 'deleted';
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
  name: string;
  icon?: string;
  order?: number;
}

export interface UpdatePointTypeData {
  name?: string;
  icon?: string;
  order?: number;
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
