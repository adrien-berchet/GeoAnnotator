/**
 * Integration tests for Markdown rendering in AnnotationList
 *
 * Tests verify the full user flow of viewing annotations with markdown content
 * and theme switching behavior.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AnnotationList } from "../../components/annotations/AnnotationList";
import type { Annotation } from "../../types/annotation";
import * as annotationsApi from "../../api/annotations";
import * as useColorModeModule from "../../hooks/useColorMode";

// Mock the annotations API
vi.mock("../../api/annotations", () => ({
  getAnnotations: vi.fn(),
  downloadAnnotation: vi.fn(),
  deleteAnnotation: vi.fn(),
}));

// Mock the useColorMode hook (will be updated dynamically in tests)
vi.mock("../../hooks/useColorMode", () => ({
  useColorMode: vi.fn(() => "light"),
}));

describe("AnnotationList - Integration Tests", () => {
  const mockPointId = "integration-test-point";

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the mock to return 'light' mode by default
    vi.mocked(useColorModeModule.useColorMode).mockReturnValue("light");
  });

  /**
   * T010: Integration test for full user flow
   */
  describe("Full User Flow", () => {
    it("should render multiple annotations with different markdown content independently", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "int-1",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# First Annotation\n\nThis has **bold** text.",
          file: null,
          order: 1,
          created_at: "2025-10-15T10:00:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
        {
          id: "int-2",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "## Second Annotation\n\n- List item 1\n- List item 2",
          file: null,
          order: 2,
          created_at: "2025-10-15T10:01:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
        {
          id: "int-3",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "[Link to docs](https://example.com/docs)",
          file: null,
          order: 3,
          created_at: "2025-10-15T10:02:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // First annotation
        const heading1 = screen.getByRole("heading", {
          level: 1,
          name: "First Annotation",
        });
        expect(heading1).toBeInTheDocument();
        const boldText = screen.getByText("bold", { selector: "strong" });
        expect(boldText).toBeInTheDocument();

        // Second annotation
        const heading2 = screen.getByRole("heading", {
          level: 2,
          name: "Second Annotation",
        });
        expect(heading2).toBeInTheDocument();
        const listItems = screen.getAllByRole("listitem");
        expect(listItems.length).toBeGreaterThanOrEqual(2);

        // Third annotation
        const link = screen.getByRole("link", { name: "Link to docs" });
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute("href", "https://example.com/docs");
      });
    });

    it("should handle mixed content types (text and file annotations)", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "int-4",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "**Text annotation** with markdown",
          file: null,
          order: 1,
          created_at: "2025-10-15T10:00:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
        {
          id: "int-5",
          gps_point_id: mockPointId,
          type: "image",
          text_content: null,
          file: {
            url: "/media/test.jpg",
            file_name: "test.jpg",
            file_size: 12345,
            mime_type: "image/jpeg",
            can_preview: true,
          },
          order: 2,
          created_at: "2025-10-15T10:01:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Text annotation should render markdown
        const boldText = screen.getByText("Text annotation", {
          selector: "strong",
        });
        expect(boldText).toBeInTheDocument();

        // File annotation should still render normally
        expect(screen.getByText(/test\.jpg/)).toBeInTheDocument();
      });
    });

    it("should maintain markdown rendering when annotations are reloaded", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "int-6",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# Initial Content\n\n**Bold** and *italic* text",
          file: null,
          order: 1,
          created_at: "2025-10-15T10:00:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Initial Content" }),
        ).toBeInTheDocument();
        expect(
          screen.getByText("Bold", { selector: "strong" }),
        ).toBeInTheDocument();
        expect(
          screen.getByText("italic", { selector: "em" }),
        ).toBeInTheDocument();
      });
    });
  });

  /**
   * Theme switching integration
   */
  describe("Theme Switching", () => {
    it("should update data-color-mode when theme changes from light to dark", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "theme-1",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# Theme Test",
          file: null,
          order: 1,
          created_at: "2025-10-15T10:00:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      // Start with light mode
      vi.mocked(useColorModeModule.useColorMode).mockReturnValue("light");
      const { rerender } = render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        const container = screen
          .getByText("Theme Test")
          .closest("[data-color-mode]");
        expect(container).toHaveAttribute("data-color-mode", "light");
      });

      // Switch to dark mode
      vi.mocked(useColorModeModule.useColorMode).mockReturnValue("dark");
      rerender(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        const container = screen
          .getByText("Theme Test")
          .closest("[data-color-mode]");
        expect(container).toHaveAttribute("data-color-mode", "dark");
      });
    });

    it("should apply theme consistently across multiple annotations", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "theme-2",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# First",
          file: null,
          order: 1,
          created_at: "2025-10-15T10:00:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
        {
          id: "theme-3",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# Second",
          file: null,
          order: 2,
          created_at: "2025-10-15T10:01:00Z",
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        },
      ];

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      vi.mocked(useColorModeModule.useColorMode).mockReturnValue("dark");
      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        const containers = screen
          .getAllByText(/First|Second/)
          .map((el) => el.closest("[data-color-mode]"));

        containers.forEach((container) => {
          expect(container).toHaveAttribute("data-color-mode", "dark");
        });
      });
    });
  });

  /**
   * Performance and edge cases
   */
  describe("Performance and Edge Cases", () => {
    it("should handle large number of annotations efficiently", async () => {
      // Generate 20 annotations with markdown
      const mockAnnotations: Annotation[] = Array.from(
        { length: 20 },
        (_, i) => ({
          id: `perf-${i}`,
          gps_point_id: mockPointId,
          type: "text" as const,
          text_content: `# Annotation ${i + 1}\n\n**Bold** and *italic* text with [link](https://example.com)`,
          file: null,
          order: i + 1,
          created_at: `2025-10-15T10:${String(i).padStart(2, "0")}:00Z`,
          is_trashed: false,
          trash_days_remaining: null,
          trash_id: null,
        }),
      );

      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue(
        mockAnnotations,
      );

      const startTime = performance.now();
      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        const headings = screen.getAllByRole("heading");
        expect(headings.length).toBeGreaterThanOrEqual(20);
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;
      const ciSafeThreshold = process.env.CI ? 2000 : 1000;

      // CI VMs are ~30% slower than local dev machines; widening the
      // threshold there keeps the guard meaningful without causing flakes.
      expect(renderTime).toBeLessThan(ciSafeThreshold);
    });

    it("should gracefully handle empty annotation list", async () => {
      vi.mocked(annotationsApi.getAnnotations).mockResolvedValue([]);

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Should show empty state message
        expect(screen.getByText(/No annotations/i)).toBeInTheDocument();
      });
    });

    it("should handle API errors gracefully", async () => {
      vi.mocked(annotationsApi.getAnnotations).mockRejectedValue(
        new Error("Failed to fetch annotations"),
      );

      render(<AnnotationList pointId={mockPointId} />);

      await waitFor(() => {
        // Should show error message
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });
});
