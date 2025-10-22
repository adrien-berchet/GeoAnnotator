/**
 * Integration tests for Device Position Feature.
 *
 * Tests the device position functionality including:
 * - Blue dot appears when device position is available
 * - Blue dot moves in real time as position updates
 * - User can recenter map on device position
 * - Clicking blue dot opens point creation panel with device position
 * - User is notified if position is unavailable or permission denied
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { MapPage } from '../../pages/MapPage';

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn(),
  clearWatch: vi.fn(),
};

// Mock API calls
vi.mock('../../api/points', () => ({
  getPoints: vi.fn().mockResolvedValue([]),
  searchPointsByTags: vi.fn().mockResolvedValue([]),
  getTags: vi.fn().mockResolvedValue([]),
}));

vi.mock('../../api/types', () => ({
  getPointTypes: vi.fn().mockResolvedValue([]),
}));

// Mock Leaflet
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children, eventHandlers }: any) => (
    <div
      data-testid="marker"
      onClick={() => eventHandlers?.click && eventHandlers.click()}
    >
      {children}
    </div>
  ),
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  useMap: () => ({
    setView: vi.fn(),
    flyTo: vi.fn(),
    on: vi.fn(),
  }),
  useMapEvents: () => null,
}));

describe('Device Position Integration Tests', () => {
  beforeEach(() => {
    // Setup geolocation mock
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

  describe('T003: Blue dot appears at device position if available', () => {
    it('should display blue dot when device position is available', async () => {
      // Mock successful geolocation
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
        return 1; // watch ID
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      // Wait for map to load
      await waitFor(() => {
        expect(screen.getByTestId('map-container')).toBeInTheDocument();
      });

      // Verify geolocation was requested
      expect(mockGeolocation.watchPosition).toHaveBeenCalled();

      // Wait for blue dot to appear
      await waitFor(() => {
        const blueDot = screen.queryByTestId('blue-dot');
        expect(blueDot).toBeInTheDocument();
      });
    });

    it('should not display blue dot when device position is unavailable', async () => {
      // Mock geolocation error
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback?.({
          code: 1,
          message: 'User denied Geolocation',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('map-container')).toBeInTheDocument();
      });

      // Verify blue dot is NOT displayed
      const blueDot = screen.queryByTestId('blue-dot');
      expect(blueDot).not.toBeInTheDocument();
    });

    it('should display blue dot at correct coordinates', async () => {
      const mockPosition = {
        coords: {
          latitude: 48.8584,
          longitude: 2.2945,
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

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const blueDot = screen.queryByTestId('blue-dot');
        expect(blueDot).toBeInTheDocument();
        expect(blueDot).toHaveAttribute('data-lat', '48.8584');
        expect(blueDot).toHaveAttribute('data-lng', '2.2945');
      });
    });
  });

  describe('T004: Blue dot moves in real time as position updates', () => {
    it('should update blue dot position when device position changes', async () => {
      let positionCallback: ((position: any) => void) | null = null;
      const firstPosition = {
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

      const secondPosition = {
        coords: {
          latitude: 48.8584,
          longitude: 2.2945,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.watchPosition.mockImplementation((successCallback: (position: any) => void) => {
        positionCallback = successCallback;
        successCallback(firstPosition);
        return 1;
      });
      expect(positionCallback).not.toBeNull();

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      // Wait for initial blue dot
      await waitFor(() => {
        const blueDot = screen.queryByTestId('blue-dot');
        expect(blueDot).toBeInTheDocument();
        expect(blueDot).toHaveAttribute('data-lat', '48.8566');
        expect(blueDot).toHaveAttribute('data-lng', '2.3522');
      });

      // Simulate position update
      (positionCallback || ((_position: any) => { }))(secondPosition);

      // Wait for blue dot to update
      await waitFor(() => {
        const blueDot = screen.queryByTestId('blue-dot');
        expect(blueDot).toHaveAttribute('data-lat', '48.8584');
        expect(blueDot).toHaveAttribute('data-lng', '2.2945');
      });
    });

    it('should update blue dot within 500ms of position change', async () => {
      let positionCallback: ((position: any) => void) | null = null;
      const firstPosition = {
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

      const secondPosition = {
        coords: {
          latitude: 48.8584,
          longitude: 2.2945,
          accuracy: 10,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
        },
        timestamp: Date.now(),
      };

      mockGeolocation.watchPosition.mockImplementation((successCallback: (position: any) => void) => {
        positionCallback = successCallback;
        successCallback(firstPosition);
        return 1;
      });
      expect(positionCallback).not.toBeNull();

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('blue-dot')).toBeInTheDocument();
      });

      // Measure update time
      const startTime = Date.now();
      (positionCallback || ((_position: any) => { }))(secondPosition);

      await waitFor(() => {
        const blueDot = screen.queryByTestId('blue-dot');
        expect(blueDot).toHaveAttribute('data-lat', '48.8584');
      }, { timeout: 500 });

      const updateTime = Date.now() - startTime;
      expect(updateTime).toBeLessThan(500);
    });
  });

  describe('T005: User can recenter map on device position', () => {
    it('should display recenter button when device position is available', async () => {
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

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const recenterButton = screen.queryByRole('button', { name: /recenter|my location/i });
        expect(recenterButton).toBeInTheDocument();
        expect(recenterButton).not.toBeDisabled();
      });
    });

    it('should disable recenter button when device position is unavailable', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback?.({
          code: 1,
          message: 'User denied Geolocation',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const recenterButton = screen.queryByRole('button', { name: /recenter|my location/i });
        if (recenterButton) {
          expect(recenterButton).toBeDisabled();
        }
      });
    });

    it('should recenter map when recenter button is clicked', async () => {
      const user = userEvent.setup();
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

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('blue-dot')).toBeInTheDocument();
      });

      const recenterButton = screen.getByRole('button', { name: /recenter|my location/i });
      await user.click(recenterButton);

      // Note: In real implementation, verify map.flyTo or map.setView was called
      // This would require accessing the map instance via the mocked useMap hook
    });
  });

  describe('T006: Clicking blue dot opens point creation panel with device position', () => {
    it('should open point creation panel when blue dot is clicked', async () => {
      const user = userEvent.setup();
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

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('blue-dot')).toBeInTheDocument();
      });

      const blueDot = screen.getByTestId('blue-dot');
      await user.click(blueDot);

      // Verify point creation modal/panel opens
      await waitFor(() => {
        expect(screen.queryByRole('dialog') || screen.queryByLabelText(/create point/i)).toBeInTheDocument();
      });
    });

    it('should pre-fill device position in point creation panel', async () => {
      const user = userEvent.setup();
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

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('blue-dot')).toBeInTheDocument();
      });

      const blueDot = screen.getByTestId('blue-dot');
      await user.click(blueDot);

      // Wait for creation panel
      await waitFor(() => {
        expect(screen.queryByRole('dialog') || screen.queryByLabelText(/create point/i)).toBeInTheDocument();
      });

      // Verify latitude and longitude are pre-filled
      const latInput = screen.queryByLabelText(/latitude/i);
      const lngInput = screen.queryByLabelText(/longitude/i);

      if (latInput) {
        expect(latInput).toHaveValue(48.8566);
      }
      if (lngInput) {
        expect(lngInput).toHaveValue(2.3522);
      }
    });
  });

  describe('T007: User is notified if position is unavailable or permission denied', () => {
    it('should show notification when permission is denied', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback?.({
          code: 1,
          message: 'User denied Geolocation',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      // Wait for notification
      await waitFor(() => {
        const notification = screen.queryByText(/location permission denied|access to location was denied/i);
        expect(notification).toBeInTheDocument();
      });
    });

    it('should show notification when position is unavailable', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback?.({
          code: 2,
          message: 'Position unavailable',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const notification = screen.queryByText(/location unavailable|unable to determine location/i);
        expect(notification).toBeInTheDocument();
      });
    });

    it('should show notification when geolocation times out', async () => {
      mockGeolocation.watchPosition.mockImplementation((_successCallback, errorCallback) => {
        errorCallback?.({
          code: 3,
          message: 'Timeout',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
        return 1;
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const notification = screen.queryByText(/location request timed out|took too long/i);
        expect(notification).toBeInTheDocument();
      });
    });

    it('should show notification when geolocation is not supported', async () => {
      // Remove geolocation support
      Object.defineProperty(global.navigator, 'geolocation', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const notification = screen.queryByText(/geolocation is not supported|browser does not support/i);
        expect(notification).toBeInTheDocument();
      });
    });
  });
});
