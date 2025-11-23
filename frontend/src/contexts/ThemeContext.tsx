/**
 * Theme context and provider for managing application theme
 */

import React, { createContext, useContext, useEffect, useState } from "react";
import { getSettings, updateSettings } from "@/api/settings";
import { useAuth } from "@/hooks/useAuth";
import type {
  ThemeMode,
  ResolvedTheme,
  ThemeContextValue,
} from "@/types/settings";
import { logger } from "@/utils/logger";

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

/**
 * Hook to access theme context
 * @throws Error if used outside ThemeProvider
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
  initialTheme?: ThemeMode;
}

/**
 * Provider component for theme management
 * Loads theme from backend on mount and persists changes
 */
export function ThemeProvider({
  children,
  initialTheme = "auto",
}: ThemeProviderProps) {
  const { user } = useAuth();
  const [themeMode, setThemeModeState] = useState<ThemeMode>(initialTheme);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() => {
    try {
      if (initialTheme === "auto") {
        return window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
      }
      return initialTheme as ResolvedTheme;
    } catch {
      return "light";
    }
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load theme from backend on mount for authenticated users
  useEffect(() => {
    const loadTheme = async () => {
      if (!user) {
        setIsLoading(false);
        return;
      }

      try {
        const settings = await getSettings();
        setThemeModeState(settings.theme_mode);
      } catch (error) {
        logger.error("Failed to load theme from backend:", error);
        // Fallback to default or initialTheme
        setThemeModeState(initialTheme);
      } finally {
        setIsLoading(false);
      }
    };

    loadTheme();
  }, [user, initialTheme]);

  // Resolve theme based on system preference
  useEffect(() => {
    const updateResolvedTheme = () => {
      if (themeMode === "auto") {
        const prefersDark = window.matchMedia(
          "(prefers-color-scheme: dark)",
        ).matches;
        setResolvedTheme(prefersDark ? "dark" : "light");
      } else {
        setResolvedTheme(themeMode);
      }
    };

    updateResolvedTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (themeMode === "auto") {
        updateResolvedTheme();
      }
    };

    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [themeMode]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolvedTheme);
  }, [resolvedTheme]);

  /**
   * Set theme mode and persist to backend for authenticated users
   */
  const setThemeMode = async (mode: ThemeMode) => {
    // Update local state immediately for responsive UI
    setThemeModeState(mode);

    // Persist to backend if user is authenticated
    if (user) {
      try {
        await updateSettings({ theme_mode: mode });
      } catch (error) {
        logger.error("Failed to persist theme to backend:", error);
        // UI already updated, so we don't revert on error
        // This provides optimistic updates for better UX
      }
    }
  };

  const value: ThemeContextValue = {
    themeMode,
    resolvedTheme,
    setThemeMode,
    isLoading,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}
