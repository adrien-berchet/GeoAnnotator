/**
 * Unit tests for useDevicePosition hook.
 *
 * Tests device position tracking, error handling, and geolocation API integration.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDevicePosition, GeolocationErrorType, getGeolocationErrorMessage } from '../useDevicePosition';

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
};

describe('useDevicePosition', () => {
  beforeEach(() => {
    Object.defineProperty(global.navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true,
      configurable: true,
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Position Tracking', () => {
    it('should return null position initially', () => {
      mockGeolocation.watchPosition.mockReturnValue(1);

      const { result } = renderHook(() => useDevicePosition());

      expect(result.current.position).toBeNull();
      expect(result.current.isLoading).toBe(true);
    });

    it('should update position when geolocation succeeds', async () => {
      const mockPosition = {
        coords: {
          latitude: 48.8566,
          longitude: 2.3522,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.watchPosition.mockImplementation((successCallback) => {
        successCallback(mockPosition);
        return 1;
      });

      const { result } = renderHook(() => useDevicePosition());

      await waitFor(() => {
        expect(result.current.position).not.toBeNull();
      });

      expect(result.current.position?.latitude).toBe(48.8566);
      expect(result.current.position?.longitude).toBe(2.3522);
      expect(result.current.position?.accuracy).toBe(10);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should request high accuracy position', () => {
      mockGeolocation.watchPosition.mockReturnValue(1);

      renderHook(() => useDevicePosition());

      expect(mockGeolocation.watchPosition).toHaveBeenCalledWith(
        expect.any(Function),
        expect.any(Function),
        expect.objectContaining({
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        })
      );
    });

    it('should cleanup watch on unmount', () => {
      const watchId = 123;
      mockGeolocation.watchPosition.mockReturnValue(watchId);

      const { unmount } = renderHook(() => useDevicePosition());

      unmount();

      expect(mockGeolocation.clearWatch).toHaveBeenCalledWith(watchId);
    });
  });

  describe('Error Handling', () => {
    it('should handle permission denied error', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback({
          code: 1,
          message: 'User denied Geolocation',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      const { result } = renderHook(() => useDevicePosition());

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.code).toBe(GeolocationErrorType.PERMISSION_DENIED);
      expect(result.current.position).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle position unavailable error', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback({
          code: 2,
          message: 'Position unavailable',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      const { result } = renderHook(() => useDevicePosition());

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.code).toBe(GeolocationErrorType.POSITION_UNAVAILABLE);
    });

    it('should handle timeout error', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback({
          code: 3,
          message: 'Timeout',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      const { result } = renderHook(() => useDevicePosition());

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.code).toBe(GeolocationErrorType.TIMEOUT);
    });

    it('should handle unsupported geolocation', async () => {
      Object.defineProperty(global.navigator, 'geolocation', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { result } = renderHook(() => useDevicePosition());

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.code).toBe(GeolocationErrorType.NOT_SUPPORTED);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('getGeolocationErrorMessage', () => {
    it('should return empty string for null error', () => {
      expect(getGeolocationErrorMessage(null)).toBe('');
    });

    it('should return permission denied message', () => {
      const error = {
        code: GeolocationErrorType.PERMISSION_DENIED,
        message: 'Permission denied',
      };

      const message = getGeolocationErrorMessage(error);

      expect(message).toContain('denied');
      expect(message).toContain('location permissions');
    });

    it('should return position unavailable message', () => {
      const error = {
        code: GeolocationErrorType.POSITION_UNAVAILABLE,
        message: 'Position unavailable',
      };

      const message = getGeolocationErrorMessage(error);

      expect(message).toContain('Unable to determine location');
    });

    it('should return timeout message', () => {
      const error = {
        code: GeolocationErrorType.TIMEOUT,
        message: 'Timeout',
      };

      const message = getGeolocationErrorMessage(error);

      expect(message).toContain('timed out');
    });

    it('should return not supported message', () => {
      const error = {
        code: GeolocationErrorType.NOT_SUPPORTED,
        message: 'Not supported',
      };

      const message = getGeolocationErrorMessage(error);

      expect(message).toContain('not supported');
    });

    it('should return default message for unknown error code', () => {
      const error = {
        code: 999 as any,
        message: 'Unknown error',
      };

      const message = getGeolocationErrorMessage(error);

      expect(message).toContain('unknown error');
    });
  });
});
