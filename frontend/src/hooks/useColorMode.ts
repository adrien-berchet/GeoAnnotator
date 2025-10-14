import { useState, useEffect } from 'react';

/**
 * Custom hook to detect and track system color mode preference.
 *
 * @returns 'light' | 'dark' based on system preference
 */
export function useColorMode(): 'light' | 'dark' {
  const [colorMode, setColorMode] = useState<'light' | 'dark'>(() => {
    // Check initial preference
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // Update state when preference changes
    const handleChange = (e: MediaQueryListEvent) => {
      setColorMode(e.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return colorMode;
}
