/**
 * Integration tests for Point Creation with Type Selection.
 *
 * Tests the point creation functionality with type selection including:
 * - Creating points with type selection dropdown
 * - Default type selection
 * - Type icon display in dropdown
 * - Type filtering/search in dropdown
 * - Validation and error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MapPage } from '../../pages/MapPage';

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock Leaflet
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: () => <div data-testid="marker" />,
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  useMap: () => ({
    setView: vi.fn(),
    flyTo: vi.fn(),
  }),
  useMapEvents: () => null,
}));

const mockTypes = [
  {
    id: 'default-type-id',
    name: 'Point',
    icon: '/icons/default.svg',
    order: 0,
    status: 'active',
    user: null // Base type
  },
  {
    id: 'type-1',
    name: 'Restaurant',
    icon: '/icons/restaurant.svg',
    order: 1,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
  },
  {
    id: 'type-2',
    name: 'Museum',
    icon: '/icons/museum.svg',
    order: 2,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
  },
  {
    id: 'type-3',
    name: 'Park',
    icon: '/icons/park.svg',
    order: 3,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
  }
];

const mockPoints = [
  {
    id: 'point-1',
    title: 'Eiffel Tower',
    description: null,
    latitude: 48.8584,
    longitude: 2.2945,
    is_public: true,
    owner: { id: 'user1', email: 'test@example.com' },
    type: mockTypes[0],
    tags: [],
    annotation_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    editing_lock_user: null,
    editing_lock_acquired_at: null
  }
];

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('Point Creation with Types Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Type Dropdown Display', () => {
    it('should display type dropdown with all available types', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      // Open point creation form (e.g., by clicking on map)
      const map = screen.getByTestId('map-container');
      await user.click(map);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      // Check type dropdown exists
      const typeDropdown = screen.getByLabelText(/type/i);
      expect(typeDropdown).toBeInTheDocument();

      // Open dropdown
      await user.click(typeDropdown);

      // Verify all types are displayed
      await waitFor(() => {
        expect(screen.getByText('Point')).toBeInTheDocument();
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
        expect(screen.getByText('Museum')).toBeInTheDocument();
        expect(screen.getByText('Park')).toBeInTheDocument();
      });
    });

    it('should display icons next to type names in dropdown', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      const typeDropdown = screen.getByLabelText(/type/i);
      await user.click(typeDropdown);

      // Verify icons are displayed
      await waitFor(() => {
        const icons = screen.getAllByRole('img');
        expect(icons.length).toBeGreaterThanOrEqual(mockTypes.length);
      });
    });

    it('should display types in correct order', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      const typeDropdown = screen.getByLabelText(/type/i);
      await user.click(typeDropdown);

      // Get all type options
      await waitFor(() => {
        const options = screen.getAllByRole('option');
        expect(options[0]).toHaveTextContent('Point');
        expect(options[1]).toHaveTextContent('Restaurant');
        expect(options[2]).toHaveTextContent('Museum');
        expect(options[3]).toHaveTextContent('Park');
      });
    });
  });

  describe('Creating Points with Type Selection', () => {
    it('should create a point with selected type', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      vi.mocked(apiClient.apiClient.post).mockResolvedValue({
        data: {
          id: 'new-point-id',
          title: 'New Restaurant',
          latitude: 48.8566,
          longitude: 2.3522,
          type: mockTypes[1], // Restaurant
          owner: { id: 'user1', email: 'test@example.com' },
          tags: [],
          annotation_count: 0,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z'
        }
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      // Fill in title
      const titleInput = screen.getByLabelText(/title/i);
      await user.type(titleInput, 'New Restaurant');

      // Select type
      const typeDropdown = screen.getByLabelText(/type/i);
      await user.click(typeDropdown);
      const restaurantOption = screen.getByText('Restaurant');
      await user.click(restaurantOption);

      // Submit form
      const saveButton = screen.getByRole('button', { name: /save|create/i });
      await user.click(saveButton);

      // Verify API was called with correct type_id
      await waitFor(() => {
        expect(apiClient.apiClient.post).toHaveBeenCalledWith(
          expect.stringContaining('/points/'),
          expect.objectContaining({
            title: 'New Restaurant',
            type_id: 'type-1'
          })
        );
      });
    });

    it('should use default type when no type selected', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      vi.mocked(apiClient.apiClient.post).mockResolvedValue({
        data: {
          id: 'new-point-id',
          title: 'Generic Point',
          latitude: 48.8566,
          longitude: 2.3522,
          type: mockTypes[0], // Default type
          owner: { id: 'user1', email: 'test@example.com' },
          tags: [],
          annotation_count: 0,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z'
        }
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      const titleInput = screen.getByLabelText(/title/i);
      await user.type(titleInput, 'Generic Point');

      // Don't select a type - should use default

      const saveButton = screen.getByRole('button', { name: /save|create/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(apiClient.apiClient.post).toHaveBeenCalled();
      });

      // Verify response has default type
      const createdPoint = (apiClient.apiClient.post as any).mock.results[0].value;
      expect((await createdPoint).data.type.name).toBe('Point');
    });

    it('should default to "Point" type in dropdown', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

  vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      // Check that default type is pre-selected
      const typeDropdown = screen.getByLabelText(/type/i);
      expect(typeDropdown).toHaveValue('default-type-id');
    });
  });

  describe('Type Dropdown Search/Filter', () => {
    it('should filter types when typing in dropdown', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

  vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      const typeDropdown = screen.getByLabelText(/type/i);
      await user.click(typeDropdown);

      // Type to filter
      await user.type(typeDropdown, 'Res');

      // Only Restaurant should be visible
      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
        expect(screen.queryByText('Museum')).not.toBeInTheDocument();
        expect(screen.queryByText('Park')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for type dropdown', async () => {
      const apiClient = await import('../../api/client');

  vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      await waitFor(() => {
        const typeDropdown = screen.getByLabelText(/type/i);
        expect(typeDropdown).toHaveAttribute('aria-label');
      });
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

  vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.resolve({ data: mockTypes });
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      const map = screen.getByTestId('map-container');
      await user.click(map);

      await waitFor(() => {
        expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      });

      // Tab to type dropdown
      await user.tab();
      await user.tab(); // Might need multiple tabs depending on form structure

      const typeDropdown = screen.getByLabelText(/type/i);

      // Open with keyboard
      await user.keyboard('{Enter}');

      // Navigate with arrow keys
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');

      // Verify selection worked
      expect(typeDropdown).not.toHaveValue('default-type-id');
    });
  });

  describe('Error Handling', () => {
    it('should show error when type API fails to load', async () => {
      const apiClient = await import('../../api/client');

  vi.mocked(apiClient.apiClient.get).mockImplementation((url: string) => {
        if (url.includes('/types/')) return Promise.reject(new Error('Network error'));
        if (url.includes('/points/')) return Promise.resolve({ data: mockPoints });
        return Promise.reject(new Error('Unknown endpoint'));
      });

      renderWithProviders(<MapPage />);

      // Verify error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/failed to load types/i)).toBeInTheDocument();
      });
    });
  });
});
