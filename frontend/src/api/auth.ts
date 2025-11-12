/**
 * Authentication API calls.
 */

import { apiClient } from "./client";
import type { User, LoginCredentials, RegisterData } from "../types/auth";

/**
 * Login response.
 */
interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

/**
 * Register response.
 */
interface RegisterResponse {
  access: string;
  refresh: string;
  user: User;
}

/**
 * Refresh response.
 */
interface RefreshResponse {
  access: string;
}

/**
 * Register new user.
 */
export async function register(data: RegisterData): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>(
    "/auth/register/",
    data,
  );
  return response.data;
}

/**
 * Login user.
 */
export async function login(
  credentials: LoginCredentials,
): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>(
    "/auth/login/",
    credentials,
  );
  return response.data;
}

/**
 * Refresh access token.
 */
export async function refreshToken(
  refreshToken: string,
): Promise<RefreshResponse> {
  const response = await apiClient.post<RefreshResponse>("/auth/refresh/", {
    refresh: refreshToken,
  });
  return response.data;
}

/**
 * Logout user.
 */
export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout/", {
    refresh: refreshToken,
  });
}

/**
 * Get current user profile.
 */
export async function getProfile(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me/");
  return response.data;
}
