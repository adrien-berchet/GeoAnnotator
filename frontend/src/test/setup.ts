import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Fix for webidl-conversions error with URL/URLSearchParams
// This ensures global URL and URLSearchParams are properly available
if (typeof globalThis.URL === 'undefined') {
  globalThis.URL = URL;
}
if (typeof globalThis.URLSearchParams === 'undefined') {
  globalThis.URLSearchParams = URLSearchParams;
}

// Mock fetch globally
global.fetch = vi.fn();

// Mock settings API globally to prevent LanguageProvider from failing
vi.mock('@/api/settings', () => ({
  getSettings: vi.fn().mockResolvedValue({
    id: 'default',
    language: 'en',
    theme_mode: 'auto',
    export_format: 'geojson',
    default_map_type: 'osm',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  }),
  updateSettings: vi.fn().mockResolvedValue({
    id: 'default',
    language: 'en',
    theme_mode: 'auto',
    export_format: 'geojson',
    default_map_type: 'osm',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  }),
}));

// Mock points API globally
vi.mock('@/api/points', () => ({
  getPoints: vi.fn().mockResolvedValue([]),
  searchPointsByTags: vi.fn().mockResolvedValue([]),
  getTags: vi.fn().mockResolvedValue([]),
  createPoint: vi.fn(),
  updatePoint: vi.fn(),
  deletePoint: vi.fn(),
}));

// Mock types API globally
vi.mock('@/api/types', () => ({
  getPointTypes: vi.fn().mockResolvedValue([]),
  createPointType: vi.fn(),
  updatePointType: vi.fn(),
  deletePointType: vi.fn(),
  reorderPointTypes: vi.fn(),
  uploadTypeIcon: vi.fn(),
  downloadTypeIcon: vi.fn(),
}));

// Mock useAuth hook globally
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    isLoading: false,
    isAuthenticated: false,
    login: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
    getAccessToken: vi.fn(),
    getRefreshToken: vi.fn(),
  })),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));
