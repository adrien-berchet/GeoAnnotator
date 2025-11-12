/**
 * Unit tests for AnnotationList component - Markdown Rendering
 *
 * Tests verify that text annotations render markdown formatting correctly.
 * All tests should FAIL initially (TDD red state) until implementation in Phase 3.3.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AnnotationList } from "../../../components/annotations/AnnotationList";
import type { Annotation } from "../../../types/annotation";
import * as annotationsApi from "../../../api/annotations";

// Mock the annotations API
vi.mock("../../../api/annotations", () => ({
  getAnnotations: vi.fn(),
  downloadAnnotation: vi.fn(),
  deleteAnnotation: vi.fn(),
}));

// Mock the useColorMode hook
vi.mock("../../../hooks/useColorMode", () => ({
  useColorMode: () => "light",
}));

describe("AnnotationList - Markdown Rendering", () => {
  const mockPointId = "test-point-123";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * T002: Test basic markdown rendering
   */
  describe("Basic Markdown Rendering", () => {
    it("should render heading from markdown syntax", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-1",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# Test Heading",
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
        // Should render as <h1> element, not raw markdown syntax
        const heading = screen.getByRole("heading", {
          level: 1,
          name: "Test Heading",
        });
        expect(heading).toBeInTheDocument();
      });
    });

    it("should render bold text from markdown syntax", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-2",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "This is **bold text** in markdown",
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
        // Should render as <strong> element
        const boldText = screen.getByText("bold text", { selector: "strong" });
        expect(boldText).toBeInTheDocument();
      });
    });

    it("should render italic text from markdown syntax", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-3",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "This is *italic text* in markdown",
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
        // Should render as <em> element
        const italicText = screen.getByText("italic text", { selector: "em" });
        expect(italicText).toBeInTheDocument();
      });
    });

    it("should render combined formatting", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-4",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "**bold** and *italic* together",
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
        const boldText = screen.getByText("bold", { selector: "strong" });
        const italicText = screen.getByText("italic", { selector: "em" });
        expect(boldText).toBeInTheDocument();
        expect(italicText).toBeInTheDocument();
      });
    });
  });

  /**
   * T003: Test link rendering
   */
  describe("Link Rendering", () => {
    it("should render links as clickable elements", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-5",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "Check out [this link](https://example.com)",
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
        const link = screen.getByRole("link", { name: "this link" });
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute("href", "https://example.com");
      });
    });

    it("should open external links in new tab", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-6",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "[External link](https://example.com)",
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
        const link = screen.getByRole("link", { name: "External link" });
        expect(link).toHaveAttribute("target", "_blank");
      });
    });

    it("should have security attributes on external links", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-7",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "[Secure link](https://example.com)",
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
        const link = screen.getByRole("link", { name: "Secure link" });
        expect(link).toHaveAttribute(
          "rel",
          expect.stringContaining("noopener"),
        );
      });
    });

    it("should render autolinks", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-8",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "Visit <https://example.com> for more",
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
        const link = screen.getByRole("link", { name: /example\.com/ });
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute("href", "https://example.com");
      });
    });
  });

  /**
   * T004: Test list rendering
   */
  describe("List Rendering", () => {
    it("should render unordered lists", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-9",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "- Item 1\n- Item 2\n- Item 3",
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
        const list = screen.getByRole("list");
        expect(list).toBeInTheDocument();
        const items = screen.getAllByRole("listitem");
        expect(items).toHaveLength(3);
      });
    });

    it("should render ordered lists", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-10",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "1. First\n2. Second\n3. Third",
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
        const list = screen.getByRole("list");
        expect(list.tagName).toBe("OL");
        const items = screen.getAllByRole("listitem");
        expect(items).toHaveLength(3);
      });
    });
  });

  /**
   * T005: Test code rendering
   */
  describe("Code Rendering", () => {
    it("should render inline code", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-11",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "Use `const x = 42;` for constants",
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
        const code = screen.getByText("const x = 42;", { selector: "code" });
        expect(code).toBeInTheDocument();
      });
    });

    it("should render code blocks with pre and code elements", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-12",
          gps_point_id: mockPointId,
          type: "text",
          text_content:
            "```javascript\nfunction test() {\n  return 42;\n}\n```",
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
        // Code blocks have syntax highlighting with spans, so we check for pre/code structure
        const preElement = screen.getByText((_content, element) => {
          return (
            element?.tagName.toLowerCase() === "pre" &&
            element?.className.includes("language-javascript")
          );
        });
        expect(preElement).toBeInTheDocument();

        // Verify code element exists inside pre
        const codeElement = preElement.querySelector("code");
        expect(codeElement).toBeInTheDocument();
        expect(codeElement?.textContent).toContain("function");
        expect(codeElement?.textContent).toContain("test");
        expect(codeElement?.textContent).toContain("return 42");
      });
    });
  });

  /**
   * T006: Test blockquotes and mixed content
   */
  describe("Blockquotes and Mixed Content", () => {
    it("should render blockquotes", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-13",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "> This is a quote\n> spanning multiple lines",
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
        const blockquote = screen.getByText(/This is a quote/, {
          selector: "blockquote *",
        });
        expect(blockquote).toBeInTheDocument();
      });
    });

    it("should render mixed markdown elements together", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-14",
          gps_point_id: mockPointId,
          type: "text",
          text_content:
            "# Heading\n\n**Bold** and *italic*\n\n- List item\n- Another item",
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
        const heading = screen.getByRole("heading", { name: "Heading" });
        const boldText = screen.getByText("Bold", { selector: "strong" });
        const italicText = screen.getByText("italic", { selector: "em" });
        const list = screen.getByRole("list");

        expect(heading).toBeInTheDocument();
        expect(boldText).toBeInTheDocument();
        expect(italicText).toBeInTheDocument();
        expect(list).toBeInTheDocument();
      });
    });
  });

  /**
   * T007: Test plain text handling
   */
  describe("Plain Text Handling", () => {
    it("should render plain text without markdown", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-15",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "This is just plain text without any markdown",
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
        const text = screen.getByText(
          "This is just plain text without any markdown",
        );
        expect(text).toBeInTheDocument();
      });
    });

    it("should not render description for null text_content", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-16",
          gps_point_id: mockPointId,
          type: "text",
          text_content: null,
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
        // Should not render the description section for null content
        expect(
          screen.queryByTestId("annotation-description"),
        ).not.toBeInTheDocument();
      });
    });

    it("should handle malformed markdown gracefully", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-17",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "**unclosed bold and *unclosed italic",
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
        // Should render without crashing
        const container = screen.getByText(/unclosed/);
        expect(container).toBeInTheDocument();
      });
    });
  });

  /**
   * T008: Test theme integration
   */
  describe("Theme Integration", () => {
    it("should apply light mode data attribute", async () => {
      const mockAnnotations: Annotation[] = [
        {
          id: "ann-18",
          gps_point_id: mockPointId,
          type: "text",
          text_content: "# Test",
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
        const container = screen.getByText("Test").closest("[data-color-mode]");
        expect(container).toHaveAttribute("data-color-mode", "light");
      });
    });
  });
});
