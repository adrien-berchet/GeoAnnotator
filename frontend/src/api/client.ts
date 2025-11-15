/**
 * Axios API client configuration.
 *
 * Provides configured axios instance with JWT authentication interceptors.
 */

import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

/**
 * Base API URL from environment or default to localhost.
 */
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Configured axios instance.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor: Add JWT token to requests.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("access_token");

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

/**
 * Response interceptor: Handle token refresh on 401 errors.
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");

        if (!refreshToken) {
          // No refresh token, redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user");
          window.location.href = "/login";
          return Promise.reject(error);
        }

        // Refresh access token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;

        // Update stored token
        localStorage.setItem("access_token", access);

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

/**
 * API error handler.
 * Extracts error message from API response.
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string;
      message?: string;
      error?: string;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      details?: any;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      [key: string]: any;
    }>;

    if (axiosError.response?.data) {
      const data = axiosError.response.data;

      // Debug: log the error structure
      console.log("Error response data:", data);
      console.log("Error status:", axiosError.response.status);

      // Check for custom error format with details field
      if (data.details) {
        // If details is an object, try to extract the first error message
        if (typeof data.details === "object" && !Array.isArray(data.details)) {
          for (const key of Object.keys(data.details)) {
            const value = data.details[key];
            if (Array.isArray(value) && value.length > 0) {
              return value[0];
            }
            if (typeof value === "string") {
              return value;
            }
          }
        }
        // If details is a string, return it
        if (typeof data.details === "string") {
          return data.details;
        }
      }

      // Check for standard error fields
      if (data.detail) {
        // Handle ErrorDetail objects from DRF (can be string, array, or object)
        if (typeof data.detail === "string") {
          return data.detail;
        }
        // If it's an array, extract the first message
        if (Array.isArray(data.detail)) {
          const firstError = data.detail[0];
          if (typeof firstError === "string") {
            return firstError;
          }
          // If it's an ErrorDetail object with a 'string' property
          if (
            typeof firstError === "object" &&
            firstError !== null &&
            "string" in firstError
          ) {
            return String(firstError.string);
          }
          return String(firstError);
        }
        // If it's an ErrorDetail object with a 'string' property
        if (
          typeof data.detail === "object" &&
          data.detail !== null &&
          "string" in data.detail
        ) {
          return String(data.detail.string);
        }
        // Last resort: convert to string
        return String(data.detail);
      }
      if (data.message && data.message !== "Invalid request data")
        return data.message;

      // Check for field-specific validation errors (e.g., { "file": ["error message"] })
      for (const key of Object.keys(data)) {
        if (key === "error" || key === "message" || key === "details") continue;

        if (Array.isArray(data[key]) && data[key].length > 0) {
          const firstError = data[key][0];
          // Could be an ErrorDetail object or string
          return typeof firstError === "string"
            ? firstError
            : String(firstError);
        }
        if (typeof data[key] === "string") {
          return data[key];
        }
      }

      return data.message || "An error occurred";
    }

    if (axiosError.message) {
      return axiosError.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unknown error occurred";
}
