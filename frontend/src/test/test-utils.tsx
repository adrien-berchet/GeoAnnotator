/**
 * Test utilities for rendering components with all necessary providers
 */

import type { ReactElement, ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import {
  BrowserRouter,
  RouterProvider,
  createMemoryRouter,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { ThemeProvider } from "@/contexts/ThemeContext";

interface AllProvidersProps {
  children: ReactNode;
  useMemoryRouter?: boolean;
  initialEntries?: string[];
}

/**
 * Wrapper component that provides all necessary contexts for testing
 */
function AllProviders({
  children,
  useMemoryRouter = false,
  initialEntries = ["/"],
}: AllProvidersProps) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  // For useMemoryRouter, create a data router to support useBlocker
  if (useMemoryRouter) {
    const router = createMemoryRouter(
      [
        {
          path: "*",
          element: children as ReactElement,
        },
      ],
      {
        initialEntries,
      },
    );

    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <LanguageProvider>
            <RouterProvider router={router} />
          </LanguageProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          <BrowserRouter>{children}</BrowserRouter>
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  useMemoryRouter?: boolean;
  initialEntries?: string[];
}

/**
 * Custom render function that wraps components with all necessary providers
 *
 * @param ui - The component to render
 * @param options - Render options including useMemoryRouter and initialEntries
 * @returns The result of render() with all providers
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    useMemoryRouter = false,
    initialEntries = ["/"],
    ...renderOptions
  }: CustomRenderOptions = {},
) {
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <AllProviders
      useMemoryRouter={useMemoryRouter}
      initialEntries={initialEntries}
    >
      {children}
    </AllProviders>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

/**
 * Custom render function for components that only need QueryClient and Router
 * (useful for components that don't use Auth or Language contexts)
 */
export function renderWithQueryClient(
  ui: ReactElement,
  options: CustomRenderOptions = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );

  return render(ui, { wrapper: Wrapper, ...options });
}

// Re-export everything from testing-library
export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
