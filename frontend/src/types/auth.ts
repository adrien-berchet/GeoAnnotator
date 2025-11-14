/**
 * Authentication types.
 */

export interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  storage_used: number;
  storage_limit: number;
  created_at?: string;
  updated_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
