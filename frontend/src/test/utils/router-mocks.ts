/**
 * React Router testing utilities.
 *
 * Provides mock functions and utilities for testing components that use React Router hooks.
 */

import { vi } from 'vitest';

/**
 * Creates a mock navigate function for testing.
 *
 * @returns A Vitest mock function that can be used to track navigation calls.
 */
export const createMockNavigate = () => {
  return vi.fn();
};

/**
 * Mock implementation of useNavigate hook.
 *
 * Usage in tests:
 * ```typescript
 * const mockNavigate = createMockNavigate();
 * vi.mock('react-router-dom', () => ({
 *   useNavigate: () => mockNavigate,
 * }));
 * ```
 */
export const mockUseNavigate = (navigateFn: ReturnType<typeof createMockNavigate>) => {
  return () => navigateFn;
};
