/**
 * Tests for settings API client.
 *
 * These tests verify that the settings API client correctly
 * fetches and updates user preferences.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getSettings, updateSettings } from '@/api/settings';
import { apiClient } from '@/api/client';
import type { UserPreferences } from '@/types/settings';

// Unmock the settings API to test the real implementation
vi.unmock('@/api/settings');

// Mock apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

const mockedApiClient = apiClient as any;

describe('Settings API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getSettings', () => {
    it('should fetch user preferences successfully', async () => {
      const mockPreferences: UserPreferences = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        language: 'en',
        theme_mode: 'dark',
        export_format: 'kml',
        created_at: '2025-10-15T00:00:00Z',
        updated_at: '2025-10-15T00:00:00Z',
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockPreferences });

      const result = await getSettings();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/settings/');
      expect(result).toEqual(mockPreferences);
    });

    it('should handle 401 unauthorized error', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' },
        },
      };

      mockedApiClient.get.mockRejectedValueOnce(error);

      await expect(getSettings()).rejects.toThrow();
    });

    it('should handle 404 not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Preferences not found' },
        },
      };

      mockedApiClient.get.mockRejectedValueOnce(error);

      await expect(getSettings()).rejects.toThrow();
    });

    it('should handle 500 server error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      mockedApiClient.get.mockRejectedValueOnce(error);

      await expect(getSettings()).rejects.toThrow();
    });

    it('should handle network error', async () => {
      const error = new Error('Network error');

      mockedApiClient.get.mockRejectedValueOnce(error);

      await expect(getSettings()).rejects.toThrow('Network error');
    });
  });

  describe('updateSettings', () => {
    it('should update user preferences successfully', async () => {
      const updates = {
        theme_mode: 'dark' as const,
        export_format: 'kml' as const,
      };

      const mockResponse: UserPreferences = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        language: 'en',
        theme_mode: 'dark',
        export_format: 'kml',
        created_at: '2025-10-15T00:00:00Z',
        updated_at: '2025-10-15T12:00:00Z',
      };

      mockedApiClient.patch.mockResolvedValueOnce({ data: mockResponse });

      const result = await updateSettings(updates);

      expect(mockedApiClient.patch).toHaveBeenCalledWith('/settings/', updates);
      expect(result).toEqual(mockResponse);
    });

    it('should send partial updates only', async () => {
      const updates = {
        theme_mode: 'light' as const,
      };

      const mockResponse: UserPreferences = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        language: 'en',
        theme_mode: 'light',
        export_format: 'geojson',
        created_at: '2025-10-15T00:00:00Z',
        updated_at: '2025-10-15T12:00:00Z',
      };

      mockedApiClient.patch.mockResolvedValueOnce({ data: mockResponse });

      const result = await updateSettings(updates);

      expect(mockedApiClient.patch).toHaveBeenCalledWith('/settings/', updates);
    });

    it('should send partial updates only', async () => {
      const updates = {
        theme_mode: 'light' as const,
      };

      const mockResponse: UserPreferences = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        language: 'en',
        theme_mode: 'light',
        export_format: 'geojson',
        created_at: '2025-10-15T00:00:00Z',
        updated_at: '2025-10-15T12:00:00Z',
      };

      mockedApiClient.patch.mockResolvedValueOnce({ data: mockResponse });

      const result = await updateSettings(updates);

      expect(mockedApiClient.patch).toHaveBeenCalledWith('/settings/', updates);
      expect(result).toEqual(mockResponse);
    });

    it('should handle 400 bad request error', async () => {
      const updates = {
        theme_mode: 'invalid_theme' as any,
      };

      const error = {
        response: {
          status: 400,
          data: { theme_mode: ['Invalid theme choice'] },
        },
      };

      mockedApiClient.patch.mockRejectedValueOnce(error);

      await expect(updateSettings(updates)).rejects.toThrow();
    });

    it('should handle 401 unauthorized error', async () => {
      const updates = {
        theme_mode: 'dark' as const,
      };

      const error = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' },
        },
      };

      mockedApiClient.patch.mockRejectedValueOnce(error);

      await expect(updateSettings(updates)).rejects.toThrow();
    });

    it('should handle 500 server error', async () => {
      const updates = {
        theme_mode: 'dark' as const,
      };

      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      mockedApiClient.patch.mockRejectedValueOnce(error);

      await expect(updateSettings(updates)).rejects.toThrow();
    });
  });
});
