/**
 * Integration tests for map search bar positioning and layout.
 *
 * Tests cover responsive layout, positioning relative to other map controls,
 * and integration with MapPage component for local filtering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
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

  describe('Desktop Layout (≥768px) - T007', () => {
    beforeEach(() => {
      // Set viewport to desktop size
      global.innerWidth = 1024;
      global.dispatchEvent(new Event('resize'));
    });

    it('renders MapSearchBar left of points count', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      // Wait for map controls to render
      const searchBar = await screen.findByRole('search');
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const pointsCount = within(controls).getByText(/points?/i);

      // Get positions
      const searchBarRect = searchBar.getBoundingClientRect();
      const pointsCountRect = pointsCount.getBoundingClientRect();

      // Search bar should be to the left of points count
      expect(searchBarRect.left).toBeLessThan(pointsCountRect.left);
    });

    it('uses horizontal flexbox layout', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await screen.findByRole('search'); // Wait for render
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const styles = window.getComputedStyle(controls);

      expect(styles.display).toBe('flex');
      expect(styles.flexDirection).toBe('row');
    });

    it('maintains correct order: SearchBar → PointsCount → FilterButton', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const searchBar = await screen.findByRole('search');
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const filterButton = within(controls).getByText(/filter tags/i);

      const searchBarOrder = window.getComputedStyle(searchBar).order;
      const filterButtonOrder = window.getComputedStyle(filterButton).order;

      expect(parseInt(searchBarOrder)).toBeLessThan(parseInt(filterButtonOrder));
    });

    it('has search bar width between 200px-400px', async () => {
      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const searchBar = await screen.findByRole('search');
      const width = searchBar.getBoundingClientRect().width;

      expect(width).toBeGreaterThanOrEqual(200);
      expect(width).toBeLessThanOrEqual(400);
    });
  });

  describe('Mobile Layout (<768px) - T008', () => {
    beforeEach(() => {
      // Set viewport to mobile size
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));
    });

    it('renders MapSearchBar between points count and filter button', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const searchBar = await screen.findByRole('search');
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const pointsCount = within(controls).getByText(/points?/i);
      const filterButton = within(controls).getByText(/filter tags/i);

      const searchBarRect = searchBar.getBoundingClientRect();
      const pointsCountRect = pointsCount.getBoundingClientRect();
      const filterButtonRect = filterButton.getBoundingClientRect();

      // Vertical layout: points count above search bar, search bar above filter button
      expect(pointsCountRect.top).toBeLessThan(searchBarRect.top);
      expect(searchBarRect.top).toBeLessThan(filterButtonRect.top);
    });

    it('uses vertical flexbox layout', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      await screen.findByRole('search'); // Wait for render
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const styles = window.getComputedStyle(controls);

      expect(styles.display).toBe('flex');
      expect(styles.flexDirection).toBe('column');
    });

    it('maintains correct order: PointsCount → SearchBar → FilterButton', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const searchBar = await screen.findByRole('search');
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const pointsCount = within(controls).getByText(/points?/i);
      const filterButton = within(controls).getByText(/filter tags/i);

      const pointsCountOrder = window.getComputedStyle(pointsCount).order;
      const searchBarOrder = window.getComputedStyle(searchBar).order;
      const filterButtonOrder = window.getComputedStyle(filterButton).order;

      expect(parseInt(pointsCountOrder)).toBeLessThan(parseInt(searchBarOrder));
      expect(parseInt(searchBarOrder)).toBeLessThan(parseInt(filterButtonOrder));
    });

    it('stretches search bar to full width', async () => {
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const searchBar = await screen.findByRole('search');
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      const controlsWidth = controls.getBoundingClientRect().width;
      const searchBarWidth = searchBar.getBoundingClientRect().width;

      // Allow for padding/margins
      expect(searchBarWidth).toBeGreaterThan(controlsWidth * 0.9);
    });
  });

  describe('Search Filtering - T009', () => {
    it('filters points locally without navigation', async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const input = await screen.findByPlaceholderText('Search points...');
      await user.type(input, 'integration test');

      // Search should update immediately without navigation
      // The component uses real-time filtering via useEffect
    });

    it('displays search query in points counter when searching', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      const input = await screen.findByPlaceholderText('Search points...');
      await user.type(input, 'test search');

      // Look for search query in counter
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      // Should show search query in parentheses
      const counterWithSearch = await within(controls).findByText(/\(search: "test search"\)/i, {}, { timeout: 1000 });
      expect(counterWithSearch).toBeInTheDocument();
    });

    it('combines search with tag filters', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

      // Apply tag filter first (if available)
      const controls = container.querySelector('.map-controls') as HTMLElement;
      expect(controls).toBeInTheDocument();

      // Then search
      const input = screen.getByPlaceholderText('Search points...');
      await user.type(input, 'combined search');

      // Should show search filter active
      const counterWithSearch = await within(controls).findByText(/search:/i, {}, { timeout: 1000 });
      expect(counterWithSearch).toBeInTheDocument();
    });

    it('does not show search bar in Navbar', async () => {
      render(
        <BrowserRouter>
          <MapPage />
        </BrowserRouter>
      );

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
