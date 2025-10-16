import { useTheme } from '../contexts/ThemeContext';

/**
 * Custom hook to get the current color mode for MDEditor.
 * Uses the resolved theme from ThemeContext.
 *
 * @returns 'light' | 'dark' based on user's theme preference
 */
export function useColorMode(): 'light' | 'dark' {
  const { resolvedTheme } = useTheme();
  return resolvedTheme;
}
