import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import {
  useDevicePosition,
  GeolocationErrorType,
} from "../../src/hooks/useDevicePosition";

const successPosition: GeolocationPosition = {
  coords: {
    latitude: 48.8566,
    longitude: 2.3522,
    accuracy: 5,
    altitude: null,
    altitudeAccuracy: null,
    heading: null,
    speed: null,
    toJSON: () => ({}),
  },
  timestamp: 1732214400000,
  toJSON: () => ({}),
};

const permissionError: GeolocationPositionError = {
  code: GeolocationErrorType.PERMISSION_DENIED,
  message: "Permission denied",
  PERMISSION_DENIED: GeolocationErrorType.PERMISSION_DENIED,
  POSITION_UNAVAILABLE: GeolocationErrorType.POSITION_UNAVAILABLE,
  TIMEOUT: GeolocationErrorType.TIMEOUT,
};

const mockGeolocation = {
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
};

const originalGeolocation = navigator.geolocation;

describe("useDevicePosition", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: mockGeolocation,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: originalGeolocation,
    });
  });

  it("subscribes to position updates and cleans up the watcher", async () => {
    mockGeolocation.watchPosition.mockImplementation((success) => {
      success(successPosition);
      return 42;
    });

    const { result, unmount } = renderHook(() => useDevicePosition());

    await waitFor(() => {
      expect(result.current.position?.latitude).toBe(48.8566);
    });

    expect(result.current.error).toBeNull();
    expect(mockGeolocation.watchPosition).toHaveBeenCalledTimes(1);

    unmount();
    expect(mockGeolocation.clearWatch).toHaveBeenCalledWith(42);
  });

  it("surfaces geolocation errors", async () => {
    mockGeolocation.watchPosition.mockImplementation((_success, error) => {
      error?.(permissionError);
      return 7;
    });

    const { result } = renderHook(() => useDevicePosition());

    await waitFor(() => {
      expect(result.current.error?.code).toBe(
        GeolocationErrorType.PERMISSION_DENIED,
      );
    });

    expect(result.current.position).toBeNull();
  });

  it("flags browsers without geolocation support", async () => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: undefined,
    });

    const { result } = renderHook(() => useDevicePosition());

    await waitFor(() => {
      expect(result.current.error?.code).toBe(
        GeolocationErrorType.NOT_SUPPORTED,
      );
    });

    expect(result.current.position).toBeNull();
  });
});
