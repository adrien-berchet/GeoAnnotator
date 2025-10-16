/**
 * Theme context and provider for managing application theme
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ThemeMode, ResolvedTheme, ThemeContextValue } from '@/types/settings';

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

/**
 * Hook to access theme context
 * @throws Error if used outside ThemeProvider
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
  initialTheme?: ThemeMode;
}

/**
 * Provider component for theme management
 */
export function ThemeProvider({ children, initialTheme = 'auto' }: ThemeProviderProps) {
  const [themeMode, setThemeMode] = useState<ThemeMode>(initialTheme);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light');

  // Resolve theme based on system preference
  useEffect(() => {
    const updateResolvedTheme = () => {
      if (themeMode === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setResolvedTheme(prefersDark ? 'dark' : 'light');
      } else {
        setResolvedTheme(themeMode);
      }
    };

    updateResolvedTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (themeMode === 'auto') {
        updateResolvedTheme();
      }
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [themeMode]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolvedTheme);
  }, [resolvedTheme]);

  const value: ThemeContextValue = {
    themeMode,
    resolvedTheme,
    setThemeMode,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
