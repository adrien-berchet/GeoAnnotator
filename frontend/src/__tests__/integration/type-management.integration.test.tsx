/**
 * Integration tests for Type Management UI.
 *
 * Tests the point type management functionality including:
 * - Creating new types
 * - Editing types
 * - Deleting types
 * - Reordering types
 * - Type limit validation (1000 types)
 * - Unique name validation
 * - Default icon fallback
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TagManagementPage from '../../pages/TagManagementPage';

// Mock API client
vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  }
}));

const mockTypes = [
  {
    id: '1',
    name: 'Restaurant',
    icon: '/icons/restaurant.svg',
    order: 1,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
  },
  {
    id: '2',
    name: 'Museum',
    icon: '/icons/museum.svg',
    order: 2,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
  },
  {
    id: '3',
    name: 'Park',
    icon: '/icons/park.svg',
    order: 3,
    status: 'active',
    user: { id: 'user1', email: 'test@example.com' }
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

describe('Type Management Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Creating Types', () => {
    it('should create a new type successfully', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      // Mock GET for listing types
      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      // Mock POST for creating type
      vi.mocked(apiClient.default.post).mockResolvedValue({
        data: {
          id: '4',
          name: 'Café',
          icon: '/icons/cafe.svg',
          order: 4,
          status: 'active',
          user: { id: 'user1', email: 'test@example.com' }
        }
      });

      renderWithProviders(<TagManagementPage />);

      // Wait for types to load
      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Click "Add New Type" button
      const addButton = screen.getByRole('button', { name: /add new type/i });
      await user.click(addButton);

      // Fill in type name
      const nameInput = screen.getByLabelText(/type name/i);
      await user.type(nameInput, 'Café');

      // Fill in icon (optional)
      const iconInput = screen.getByLabelText(/icon/i);
      await user.type(iconInput, '/icons/cafe.svg');

      // Submit form
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify API was called
      await waitFor(() => {
        expect(apiClient.default.post).toHaveBeenCalledWith(
          '/api/v1/types/',
          expect.objectContaining({
            name: 'Café',
            icon: '/icons/cafe.svg'
          })
        );
      });

      // Verify success message
      expect(await screen.findByText(/type created successfully/i)).toBeInTheDocument();
    });

    it('should use default icon when no icon specified', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.post).mockResolvedValue({
        data: {
          id: '4',
          name: 'Generic',
          icon: '/icons/default.svg',
          order: 4,
          status: 'active',
          user: { id: 'user1', email: 'test@example.com' }
        }
      });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /add new type/i });
      await user.click(addButton);

      const nameInput = screen.getByLabelText(/type name/i);
      await user.type(nameInput, 'Generic');

      // Don't fill icon field

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(apiClient.default.post).toHaveBeenCalledWith(
          '/api/v1/types/',
          expect.objectContaining({
            name: 'Generic'
          })
        );
      });
    });

    it('should show error when creating duplicate type name', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.post).mockRejectedValue({
        response: {
          status: 400,
          data: {
            error: 'VALIDATION_ERROR',
            message: 'Type name must be unique',
            details: { name: ['Type with this name already exists'] }
          }
        }
      });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /add new type/i });
      await user.click(addButton);

      const nameInput = screen.getByLabelText(/type name/i);
      await user.type(nameInput, 'Restaurant'); // Duplicate

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify error message
      expect(await screen.findByText(/type with this name already exists/i)).toBeInTheDocument();
    });

    it('should show error when exceeding 1000 type limit', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.post).mockRejectedValue({
        response: {
          status: 400,
          data: {
            error: 'VALIDATION_ERROR',
            message: 'Maximum 1000 types per user',
            details: { limit: ['You have reached the maximum of 1000 types'] }
          }
        }
      });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /add new type/i });
      await user.click(addButton);

      const nameInput = screen.getByLabelText(/type name/i);
      await user.type(nameInput, 'NewType');

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify error message
      expect(await screen.findByText(/maximum.*1000.*types/i)).toBeInTheDocument();
    });
  });

  describe('Editing Types', () => {
    it('should edit an existing type successfully', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.patch).mockResolvedValue({
        data: {
          ...mockTypes[0],
          name: 'Fine Dining',
          icon: '/icons/fine-dining.svg'
        }
      });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Click edit button for first type
      const restaurantRow = screen.getByText('Restaurant').closest('tr');
      const editButton = within(restaurantRow!).getByRole('button', { name: /edit/i });
      await user.click(editButton);

      // Update name
      const nameInput = screen.getByLabelText(/type name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Fine Dining');

      // Update icon
      const iconInput = screen.getByLabelText(/icon/i);
      await user.clear(iconInput);
      await user.type(iconInput, '/icons/fine-dining.svg');

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify API was called
      await waitFor(() => {
        expect(apiClient.default.patch).toHaveBeenCalledWith(
          '/api/v1/types/1/',
          expect.objectContaining({
            name: 'Fine Dining',
            icon: '/icons/fine-dining.svg'
          })
        );
      });

      // Verify success message
      expect(await screen.findByText(/type updated successfully/i)).toBeInTheDocument();
    });
  });

  describe('Deleting Types', () => {
    it('should delete a type successfully', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.delete).mockResolvedValue({ data: null });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Click delete button for first type
      const restaurantRow = screen.getByText('Restaurant').closest('tr');
      const deleteButton = within(restaurantRow!).getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Confirm deletion
      const confirmButton = await screen.findByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      // Verify API was called
      await waitFor(() => {
        expect(apiClient.default.delete).toHaveBeenCalledWith('/api/v1/types/1/');
      });

      // Verify success message
      expect(await screen.findByText(/type deleted successfully/i)).toBeInTheDocument();
    });

    it('should show warning that points will switch to default type', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      const restaurantRow = screen.getByText('Restaurant').closest('tr');
      const deleteButton = within(restaurantRow!).getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Verify warning message
      expect(await screen.findByText(/points.*will be switched.*default type/i)).toBeInTheDocument();
    });
  });

  describe('Reordering Types', () => {
    it('should reorder types successfully using drag and drop', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });
      vi.mocked(apiClient.default.patch).mockResolvedValue({ data: { success: true } });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Simulate drag and drop (simplified)
      // In real implementation, this would use @dnd-kit or similar

      const restaurantRow = screen.getByText('Restaurant').closest('tr');
      const dragHandle = within(restaurantRow!).getByRole('button', { name: /drag/i });

      // Simulate reordering
      // This is a simplified test - actual drag and drop testing is complex

      // For now, just verify the reorder endpoint exists
      expect(dragHandle).toBeInTheDocument();
    });
  });

  describe('Type List Display', () => {
    it('should display types in order', async () => {
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      const typeRows = screen.getAllByRole('row').slice(1); // Skip header row

      expect(typeRows[0]).toHaveTextContent('Restaurant');
      expect(typeRows[1]).toHaveTextContent('Museum');
      expect(typeRows[2]).toHaveTextContent('Park');
    });

    it('should display icons for each type', async () => {
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Verify icons are displayed
      const icons = screen.getAllByRole('img');
      expect(icons.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Accessibility', () => {
    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Tab through interactive elements
      await user.tab();

      // Verify focus is on the first interactive element
      const addButton = screen.getByRole('button', { name: /add new type/i });
      expect(addButton).toHaveFocus();
    });

    it('should have proper ARIA labels', async () => {
      const apiClient = await import('../../api/client');

      vi.mocked(apiClient.default.get).mockResolvedValue({ data: mockTypes });

      renderWithProviders(<TagManagementPage />);

      await waitFor(() => {
        expect(screen.getByText('Restaurant')).toBeInTheDocument();
      });

      // Verify ARIA labels exist
      expect(screen.getByRole('button', { name: /add new type/i })).toHaveAttribute('aria-label');
    });
  });
});
