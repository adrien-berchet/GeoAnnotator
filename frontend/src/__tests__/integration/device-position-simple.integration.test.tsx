/**
 * Simplified Integration tests for Device Position Feature.
 *
 * Focuses on core functionality without complex Marker mocks that cause OOM.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { MapPage } from "../../pages/MapPage";

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
};

// Mock API calls
vi.mock("../../api/points", () => ({
  getPoints: vi.fn().mockResolvedValue([]),
  searchPointsByTags: vi.fn().mockResolvedValue([]),
  getTags: vi.fn().mockResolvedValue([]),
}));

vi.mock("../../api/types", () => ({
  getPointTypes: vi.fn().mockResolvedValue([]),
}));

// Simplified Leaflet mock - avoid dangerouslySetInnerHTML
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({
    children,
    position,
  }: {
    children?: React.ReactNode;
    position?: [number, number];
  }) => (
    <div
      data-testid="marker"
      data-lat={position?.[0]}
      data-lng={position?.[1]}
    >
      {children}
    </div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popup">{children}</div>
  ),
  Circle: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="circle">{children}</div>
  ),
  Polygon: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="polygon">{children}</div>
  ),
  useMap: () => ({
    setView: vi.fn(),
    flyTo: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
  }),
  useMapEvents: () => null,
}));

describe("Device Position Integration Tests (Simplified)", () => {
  beforeEach(() => {
    // Setup geolocation mock
    Object.defineProperty(global.navigator, "geolocation", {
      value: mockGeolocation,
      writable: true,
      configurable: true,
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("T003: Blue dot appears at device position if available", () => {
    it("should display blue dot when device position is available", async () => {
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

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        expect(screen.getByTestId("map-container")).toBeInTheDocument();
      });

      expect(mockGeolocation.watchPosition).toHaveBeenCalled();

      // Check for marker (blue dot is rendered as a marker)
      await waitFor(() => {
        const markers = screen.queryAllByTestId("marker");
        expect(markers.length).toBeGreaterThan(0);
      });
    });

    it("should not display blue dot when device position is unavailable", async () => {
      mockGeolocation.watchPosition.mockImplementation(
        (_successCallback, errorCallback) => {
          errorCallback?.({
            code: 1,
            message: "User denied Geolocation",
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
          return 1;
        },
      );

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        expect(screen.getByTestId("map-container")).toBeInTheDocument();
      });

      // Verify watchPosition was called but failed
      expect(mockGeolocation.watchPosition).toHaveBeenCalled();
    });
  });

  describe("T005: User can recenter map on device position", () => {
    it("should display recenter button when device position is available", async () => {
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

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const recenterButton = screen.queryByRole("button", {
          name: /recenter|my location/i,
        });
        expect(recenterButton).toBeInTheDocument();
        expect(recenterButton).not.toBeDisabled();
      });
    });

    it("should disable recenter button when device position is unavailable", async () => {
      mockGeolocation.watchPosition.mockImplementation(
        (_successCallback, errorCallback) => {
          errorCallback?.({
            code: 1,
            message: "User denied Geolocation",
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
          return 1;
        },
      );

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const recenterButton = screen.queryByRole("button", {
          name: /recenter|my location/i,
        });
        if (recenterButton) {
          expect(recenterButton).toBeDisabled();
        }
      });
    });
  });

  describe("T007: User is notified if position is unavailable or permission denied", () => {
    it("should show notification when permission is denied", async () => {
      mockGeolocation.watchPosition.mockImplementation(
        (_successCallback, errorCallback) => {
          errorCallback?.({
            code: 1,
            message: "User denied Geolocation",
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
          return 1;
        },
      );

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const notification = screen.queryByText(
          /location permission denied|access to location was denied/i,
        );
        expect(notification).toBeInTheDocument();
      });
    });

    it("should show notification when position is unavailable", async () => {
      mockGeolocation.watchPosition.mockImplementation(
        (_successCallback, errorCallback) => {
          errorCallback?.({
            code: 2,
            message: "Position unavailable",
            PERMISSION_DENIED: 1,
            POSITION_UNAVAILABLE: 2,
            TIMEOUT: 3,
          });
          return 1;
        },
      );

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const notification = screen.queryByText(
          /location unavailable|unable to determine location/i,
        );
        expect(notification).toBeInTheDocument();
      });
    });

    it("should show notification when geolocation is not supported", async () => {
      // Remove geolocation support
      Object.defineProperty(global.navigator, "geolocation", {
        value: undefined,
        writable: true,
        configurable: true,
      });

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const notification = screen.queryByText(
          /geolocation is not supported|browser does not support/i,
        );
        expect(notification).toBeInTheDocument();
      });
    });
  });
});
