/**
 * Settings types for user preferences
 */

/**
 * Theme mode options for the application
 */
export type ThemeMode = 'auto' | 'light' | 'dark';

/**
 * Data export format options
 */
export type ExportFormat = 'geojson' | 'kml' | 'csv';

/**
 * Resolved theme mode (auto resolved to light or dark)
 */
export type ResolvedTheme = 'light' | 'dark';

/**
 * User preferences stored on the backend
 */
export interface UserPreferences {
  id: string;
  theme_mode: ThemeMode;
  language: string;
  export_format: ExportFormat;
  created_at: string;
  updated_at: string;
}

/**
 * Theme context value provided to components
 */
export interface ThemeContextValue {
  themeMode: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setThemeMode: (mode: ThemeMode) => void;
}
