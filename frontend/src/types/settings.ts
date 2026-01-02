/**
 * Settings types for user preferences
 */

/**
 * Theme mode options for the application
 */
export type ThemeMode = "auto" | "light" | "dark";

/**
 * Data export format options (used on import/export flows)
 */
export type ExportFormat = "geojson" | "gpx" | "kml" | "csv" | "zip";

/**
 * Map type options
 */
export type MapType = "osm" | "satellite" | "topo" | "cycle";

/**
 * Resolved theme mode (auto resolved to light or dark)
 */
export type ResolvedTheme = "light" | "dark";

/**
 * User preferences stored on the backend
 */
export interface UserPreferences {
  id: string;
  theme_mode: ThemeMode;
  language: string;
  default_map_type: MapType;
  created_at: string;
  updated_at: string;
}

/**
 * Theme context value provided to components
 */
export interface ThemeContextValue {
  themeMode: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setThemeMode: (mode: ThemeMode) => Promise<void>;
  isLoading: boolean;
}
