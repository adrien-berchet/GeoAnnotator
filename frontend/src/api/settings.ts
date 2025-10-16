/**
 * Settings API client
 */

import { apiClient } from './client';
import type { UserPreferences } from '@/types/settings';

/**
 * Fetch user settings from the backend
 * @returns User preferences object
 * @throws Error if request fails
 */
export async function getSettings(): Promise<UserPreferences> {
  const response = await apiClient.get<UserPreferences>('/settings/');
  return response.data;
}

/**
 * Update user settings on the backend
 * @param updates - Partial user preferences to update
 * @returns Updated user preferences object
 * @throws Error if request fails
 */
export async function updateSettings(
  updates: Partial<Pick<UserPreferences, 'theme_mode' | 'language' | 'export_format'>>
): Promise<UserPreferences> {
  const response = await apiClient.patch<UserPreferences>(
    '/settings/',
    updates
  );
  return response.data;
}
