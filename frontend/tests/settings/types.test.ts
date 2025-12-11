/**
 * Tests for settings type definitions.
 */
import { describe, it, expect } from "vitest";
import type {
  UserPreferences,
  ThemeMode,
  ExportFormat,
  MapType,
  ResolvedTheme,
  ThemeContextValue,
} from "@/types/settings";

describe("Settings Types", () => {
  describe("UserPreferences interface", () => {
    it("requires all persisted preference fields", () => {
      const preferences: UserPreferences = {
        id: "123e4567-e89b-12d3-a456-426614174000",
        language: "en",
        theme_mode: "auto",
        default_map_type: "osm",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      expect(preferences.id).toBeDefined();
      expect(preferences.language).toBe("en");
      expect(preferences.theme_mode).toBe("auto");
      expect(preferences.default_map_type).toBe("osm");
      expect(preferences.created_at).toBeDefined();
      expect(preferences.updated_at).toBeDefined();
    });
  });

  describe("ThemeMode type", () => {
    it("accepts supported theme options", () => {
      const auto: ThemeMode = "auto";
      const light: ThemeMode = "light";
      const dark: ThemeMode = "dark";

      expect([auto, light, dark]).toEqual(["auto", "light", "dark"]);
    });
  });

  describe("ExportFormat type", () => {
    it("accepts supported export formats", () => {
      const geojson: ExportFormat = "geojson";
      const kml: ExportFormat = "kml";
      const csv: ExportFormat = "csv";

      expect([geojson, kml, csv]).toEqual(["geojson", "kml", "csv"]);
    });
  });

  describe("MapType type", () => {
    it("accepts supported map types", () => {
      const osm: MapType = "osm";
      const satellite: MapType = "satellite";
      const topo: MapType = "topo";

      expect([osm, satellite, topo]).toEqual(["osm", "satellite", "topo"]);
    });
  });

  describe("ResolvedTheme type", () => {
    it("restricts to light or dark", () => {
      const light: ResolvedTheme = "light";
      const dark: ResolvedTheme = "dark";

      expect([light, dark]).toEqual(["light", "dark"]);
    });
  });

  describe("ThemeContextValue interface", () => {
    it("exposes theme state and setter", () => {
      const themeContext: ThemeContextValue = {
        themeMode: "auto",
        resolvedTheme: "light",
        setThemeMode: async () => {},
        isLoading: false,
      };

      expect(themeContext.themeMode).toBe("auto");
      expect(themeContext.resolvedTheme).toBe("light");
      expect(typeof themeContext.setThemeMode).toBe("function");
      expect(themeContext.isLoading).toBe(false);
    });
  });
});
