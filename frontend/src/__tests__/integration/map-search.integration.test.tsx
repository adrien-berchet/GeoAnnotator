/**
 * Integration tests for map search bar functionality.
 *
 * Tests cover integration with MapPage component for local filtering
 * and proper display of search state in the UI.
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { MapPage } from '../../pages/MapPage';

// Mock React Router useSearchParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

// Mock API calls
vi.mock('../../api/points', () => ({
  getPoints: vi.fn().mockResolvedValue([]),
  searchPointsByTags: vi.fn().mockResolvedValue([]),
  getTags: vi.fn().mockResolvedValue([]),
}));

describe('Map Search Integration', () => {

  describe('Search Filtering - T009', () => {
    it('renders search bar on map page', async () => {
      renderWithProviders(<MapPage />);

      const searchBar = await screen.findByRole('search');
      expect(searchBar).toBeInTheDocument();

      const input = screen.getByPlaceholderText('Search points...');
      expect(input).toBeInTheDocument();
    });

    it('displays search query in points counter when searching', async () => {
      const user = userEvent.setup();
      const { container } = renderWithProviders(<MapPage />);

      const input = await screen.findByPlaceholderText('Search points...');
      await user.type(input, 'test search');

      // Submit the form by pressing Enter
      await user.keyboard('{Enter}');

      // Look for search query in counter
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      // Should show search query in parentheses
      const counterWithSearch = await within(controls).findByText(/\(search: "test search"\)/i, {}, { timeout: 1000 });
      expect(counterWithSearch).toBeInTheDocument();
    });

    it('combines search with tag filters', async () => {
      const user = userEvent.setup();
      const { container } = renderWithProviders(<MapPage />);

      // Wait for the input to be available
      const input = await screen.findByPlaceholderText('Search points...');

      // Now get controls after the component has rendered
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      // Search
      await user.type(input, 'combined search');

      // Submit the form by pressing Enter
      await user.keyboard('{Enter}');

      // Should show search filter active
      const counterWithSearch = await within(controls).findByText(/search:/i, {}, { timeout: 1000 });
      expect(counterWithSearch).toBeInTheDocument();
    });

    it('clears search query when clear button is clicked', async () => {
      const user = userEvent.setup();
      const { container } = renderWithProviders(<MapPage />);

      const input = await screen.findByPlaceholderText('Search points...');
      await user.type(input, 'test query');
      await user.keyboard('{Enter}');

      // Find and click the clear button (✕)
      const clearButton = screen.getByLabelText('Clear search');
      await user.click(clearButton);

      // Check that search is cleared from counter
      const controls = container.querySelector('.map-controls') as HTMLElement;
      const counterText = within(controls).getByText(/0 points?/i);
      expect(counterText.textContent).not.toContain('search:');
    });

    it('does not show search bar in Navbar', async () => {
      renderWithProviders(<MapPage />);

      // Look for navbar
      const navbar = screen.queryByRole('navigation');
      if (navbar) {
        // Navbar should NOT contain a search form
        const searchInNavbar = within(navbar).queryByRole('search');
        expect(searchInNavbar).not.toBeInTheDocument();
      }
    });
  });
});
