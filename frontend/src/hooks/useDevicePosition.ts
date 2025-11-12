/**
 * Hook for tracking device position using browser geolocation API.
 *
 * Provides real-time device position updates and error handling for
 * permission denied, position unavailable, and timeout scenarios.
 */

import { useState, useEffect, useCallback } from "react";

/**
 * Device position coordinates.
 */
export interface DevicePosition {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
  heading: number | null; // Compass direction in degrees (0-360), null if not available
}

/**
 * Geolocation error types.
 */
export const GeolocationErrorType = {
  PERMISSION_DENIED: 1,
  POSITION_UNAVAILABLE: 2,
  TIMEOUT: 3,
  NOT_SUPPORTED: 4,
} as const;

export type GeolocationErrorTypeValue =
  (typeof GeolocationErrorType)[keyof typeof GeolocationErrorType];

/**
 * Geolocation error information.
 */
export interface GeolocationError {
  code: GeolocationErrorTypeValue;
  message: string;
}

/**
 * Hook return type.
 */
export interface UseDevicePositionReturn {
  position: DevicePosition | null;
  error: GeolocationError | null;
  isLoading: boolean;
  recenter: () => void;
}

/**
 * Hook to track device position in real time.
 *
 * @returns Device position state and error information
 */
export function useDevicePosition(): UseDevicePositionReturn {
  const [position, setPosition] = useState<DevicePosition | null>(null);
  const [error, setError] = useState<GeolocationError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Handle successful geolocation.
   */
  const handleSuccess = useCallback((pos: GeolocationPosition) => {
    const newPosition: DevicePosition = {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
      timestamp: pos.timestamp,
      heading: pos.coords.heading, // Compass direction (0-360 degrees), null if not available
    };

    setPosition(newPosition);
    setError(null);
    setIsLoading(false);
  }, []);

  /**
   * Handle geolocation error.
   */
  const handleError = useCallback((err: GeolocationPositionError) => {
    const geolocationError: GeolocationError = {
      code: err.code as GeolocationErrorTypeValue,
      message: err.message,
    };

    setError(geolocationError);
    setPosition(null);
    setIsLoading(false);
  }, []);

  /**
   * Trigger map recenter to current device position.
   */
  const recenter = useCallback(() => {
    // This function can be used if needed for future recenter logic
  }, []);

  /**
   * Setup geolocation watching on mount.
   */
  useEffect(() => {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
      setError({
        code: GeolocationErrorType.NOT_SUPPORTED,
        message: "Geolocation is not supported by this browser",
      });
      setIsLoading(false);
      return;
    }

    // Watch position with high accuracy
    const options: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    };

    const id = navigator.geolocation.watchPosition(
      handleSuccess,
      handleError,
      options,
    );

    // Cleanup: clear watch on unmount
    return () => {
      if (id !== null) {
        navigator.geolocation.clearWatch(id);
      }
    };
  }, [handleSuccess, handleError]);

  return {
    position,
    error,
    isLoading,
    recenter,
  };
}

/**
 * Get user-friendly error message for geolocation error.
 *
 * @param error - Geolocation error
 * @returns User-friendly error message
 */
export function getGeolocationErrorMessage(
  error: GeolocationError | null,
): string {
  if (!error) return "";

  switch (error.code) {
    case GeolocationErrorType.PERMISSION_DENIED:
      return "Access to location was denied. Please enable location permissions in your browser settings.";
    case GeolocationErrorType.POSITION_UNAVAILABLE:
      return "Unable to determine location. Please check your device settings.";
    case GeolocationErrorType.TIMEOUT:
      return "Location request timed out. Please try again.";
    case GeolocationErrorType.NOT_SUPPORTED:
      return "Geolocation is not supported by this browser.";
    default:
      return "An unknown error occurred while retrieving location.";
  }
}
