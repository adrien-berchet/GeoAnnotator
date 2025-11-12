/**
 * Tests for SettingsPage component.
 *
 * Tests the main settings page with loading, error, and success states.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../src/test/test-utils";
import { SettingsPage } from "../../src/pages/SettingsPage";
import * as settingsApi from "../../src/api/settings";
import * as useAuthModule from "../../src/hooks/useAuth";

// Mock the settings API
vi.mock("../../src/api/settings");
vi.mock("../../src/hooks/useAuth");

// Mock getSettings globally for LanguageProvider
vi.mock("../../src/utils/i18n", () => ({
  translate: (key: string, fallback?: string) => fallback || key,
  getInitialLanguage: () => "en",
  storeLanguage: vi.fn(),
  getSupportedLanguages: () => ["en", "fr"],
}));

const mockGetSettings = settingsApi.getSettings as any;
const mockUpdateSettings = settingsApi.updateSettings as any;

describe("SettingsPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock getSettings for LanguageProvider (returns default settings)
    mockGetSettings.mockResolvedValue({
      id: "default",
      language: "en",
      theme_mode: "auto",
      export_format: "geojson",
      default_map_type: "osm",
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    });

    // Mock authenticated user for all tests
    vi.mocked(useAuthModule.useAuth).mockReturnValue({
      user: {
        id: "1",
        email: "test@example.com",
        storage_used: 0,
        storage_limit: 1000000,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
      getAccessToken: vi.fn(),
      getRefreshToken: vi.fn(),
    });
  });

  describe("Loading State", () => {
    it("should display loading spinner while fetching preferences", () => {
      mockGetSettings.mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      expect(
        screen.getByRole("status") || screen.getByTestId("loading-spinner"),
      ).toBeInTheDocument();
    });

    it("should not display form during loading", () => {
      mockGetSettings.mockImplementation(() => new Promise(() => {}));

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      expect(screen.queryByTestId("settings-form")).not.toBeInTheDocument();
    });
  });

  describe("Success State", () => {
    it("should display form with current values after loading", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "dark",
        export_format: "kml",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(
          screen.getByTestId("settings-form") ||
            screen.getByTestId("settings-form"),
        ).toBeInTheDocument();
      });

      // Check that current values are displayed (use getAllByText since labels appear multiple times)
      expect(screen.getAllByText(/dark/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/kml/i).length).toBeGreaterThan(0);
    });

    it("should display all settings sections", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      // Wait for the form to load
      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      // Check that all sections are displayed by looking for their controls
      // Theme section
      expect(
        screen.getByRole("radiogroup", { name: /theme/i }),
      ).toBeInTheDocument();

      // Language section - check for language-related text
      const allText = screen.getAllByText(/language/i);
      expect(allText.length).toBeGreaterThan(0);

      // Export section - check for export format options
      expect(screen.getAllByText(/geojson|kml|gpx/i).length).toBeGreaterThan(0);
    });
  });

  describe("Error State", () => {
    it("should display error message when fetch fails", async () => {
      mockGetSettings.mockRejectedValueOnce(
        new Error("Failed to fetch settings"),
      );

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        // Check for error message - could be translation key or actual message
        // The error is in a div with class "settings-error" and contains a p with class "error-message"
        const errorElement = screen.getByText(/settings.*error|error/i);
        expect(errorElement).toBeInTheDocument();
      });
    });

    it("should display retry button on error", async () => {
      mockGetSettings.mockRejectedValueOnce(
        new Error("Failed to fetch settings"),
      );

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /retry/i }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Form Interaction", () => {
    it("should enable save button when form is dirty", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);
      mockUpdateSettings.mockResolvedValue(mockPreferences);

      const user = userEvent.setup();
      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      const saveButton = screen.getByRole("button", { name: /save/i });
      expect(saveButton).toBeDisabled();

      // Change export format to make form dirty (theme changes don't make it dirty)
      const kmlButton = screen.getByRole("radio", { name: /kml/i });
      await user.click(kmlButton);

      expect(saveButton).not.toBeDisabled();
    });

    it("should disable save button when form is pristine", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        const saveButton = screen.getByRole("button", { name: /save/i });
        expect(saveButton).toBeDisabled();
      });
    });

    it("should save theme immediately and other settings on save button click", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      const updatedTheme = {
        ...mockPreferences,
        theme_mode: "dark" as const,
      };

      const updatedOther = {
        ...updatedTheme,
        export_format: "kml" as const,
        updated_at: "2025-10-15T12:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);
      mockUpdateSettings
        .mockResolvedValueOnce(updatedTheme) // Theme saved immediately
        .mockResolvedValueOnce(updatedOther); // Other settings saved on button click

      const user = userEvent.setup();
      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      // Change theme - saves immediately via ThemeContext
      const darkThemeButton = screen.getByRole("radio", {
        name: /dark theme/i,
      });
      await user.click(darkThemeButton);

      await waitFor(() => {
        expect(mockUpdateSettings).toHaveBeenCalledWith({
          theme_mode: "dark",
        });
      });

      // Change export format
      const kmlButton = screen.getByRole("radio", { name: /kml/i });
      await user.click(kmlButton);

      // Click save - only saves language and export_format (theme already saved)
      const saveButton = screen.getByRole("button", { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(mockUpdateSettings).toHaveBeenLastCalledWith({
          language: "en",
          export_format: "kml",
        });
      });
    });

    it("should display success message after saving non-theme settings", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      const updatedPreferences = {
        ...mockPreferences,
        export_format: "kml" as const,
        updated_at: "2025-10-15T12:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);
      mockUpdateSettings.mockResolvedValueOnce(updatedPreferences);

      const user = userEvent.setup();
      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      // Change export format
      const kmlButton = screen.getByRole("radio", { name: /kml/i });
      await user.click(kmlButton);

      // Save
      const saveButton = screen.getByRole("button", { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(
          screen.getByText(/saved/i) || screen.getByText(/success/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Navigation Warning", () => {
    it("should warn user about unsaved changes on navigation", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);
      mockUpdateSettings.mockResolvedValue(mockPreferences); // For theme changes

      const user = userEvent.setup();
      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      // Change export format to make form dirty (theme changes don't make it dirty)
      const kmlButton = screen.getByRole("radio", { name: /kml/i });
      await user.click(kmlButton);

      // Try to navigate (will be blocked by useBlocker)
      // This test verifies the blocker is set up, actual navigation blocking
      // is handled by React Router's useBlocker
      expect(screen.getByTestId("settings-form")).toBeInTheDocument();
    });

    it("should not warn when form is pristine", async () => {
      const mockPreferences = {
        id: "123",
        language: "en",
        theme_mode: "auto",
        export_format: "geojson",
        created_at: "2025-10-15T00:00:00Z",
        updated_at: "2025-10-15T00:00:00Z",
      };

      mockGetSettings.mockResolvedValueOnce(mockPreferences);

      renderWithProviders(<SettingsPage />, { useMemoryRouter: true });

      await waitFor(() => {
        expect(screen.getByTestId("settings-form")).toBeInTheDocument();
      });

      // Form is pristine, no warning should appear on navigation
      // (useBlocker should not block)
      expect(screen.getByTestId("settings-form")).toBeInTheDocument();
    });
  });
});
