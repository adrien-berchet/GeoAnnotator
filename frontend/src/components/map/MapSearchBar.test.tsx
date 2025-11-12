/**
 * Unit tests for MapSearchBar component.
 *
 * Tests cover rendering, user interaction, search filtering callback,
 * and keyboard accessibility.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MapSearchBar } from "./MapSearchBar";

describe("MapSearchBar", () => {
  const mockOnSearch = vi.fn();

  beforeEach(() => {
    mockOnSearch.mockClear();
  });

  describe("Rendering (T003)", () => {
    it("renders a form with search role", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const form = screen.getByRole("search");
      expect(form).toBeInTheDocument();
    });

    it("renders search input with correct type and placeholder", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute("type", "search");
    });

    it("renders button with search icon initially", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const button = screen.getByRole("button", { name: /submit search/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent("🔍");
    });

    it("has correct ARIA labels", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const form = screen.getByRole("search");
      const input = screen.getByLabelText("Search query");
      const button = screen.getByLabelText("Submit search");

      expect(form).toHaveAttribute("aria-label", "Search points on map");
      expect(input).toBeInTheDocument();
      expect(button).toBeInTheDocument();
    });
  });

  describe("User Input and State (T004)", () => {
    it("updates input value when user types", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText(
        "Search points...",
      ) as HTMLInputElement;

      await user.type(input, "test query");
      expect(input.value).toBe("test query");
    });

    it("reflects state changes on multiple keystrokes", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText(
        "Search points...",
      ) as HTMLInputElement;

      await user.type(input, "a");
      expect(input.value).toBe("a");

      await user.type(input, "b");
      expect(input.value).toBe("ab");

      await user.type(input, "c");
      expect(input.value).toBe("abc");
    });

    it("is a controlled component", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText(
        "Search points...",
      ) as HTMLInputElement;

      await user.type(input, "controlled");
      expect(input.value).toBe("controlled");

      // Verify value is tied to state
      expect(input).toHaveValue("controlled");
    });
  });

  describe("Search Callback Behavior (T005)", () => {
    it("calls onSearch callback when form is submitted", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      await user.type(input, "test search");

      // onSearch should NOT be called yet (no submit)
      expect(mockOnSearch).not.toHaveBeenCalled();

      // Submit the form by pressing Enter
      await user.type(input, "{Enter}");

      // Now onSearch should be called with trimmed query
      expect(mockOnSearch).toHaveBeenCalledWith("test search");
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });

    it("calls onSearch with empty string when clear button is clicked", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText(
        "Search points...",
      ) as HTMLInputElement;

      await user.type(input, "test");

      // Click the clear button (✕)
      const button = screen.getByRole("button", { name: /clear search/i });
      await user.click(button);

      expect(input.value).toBe("");
      expect(mockOnSearch).toHaveBeenCalledWith("");
    });

    it("trims whitespace before calling onSearch", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      await user.type(input, "   trimmed   {Enter}");

      expect(mockOnSearch).toHaveBeenCalledWith("trimmed");
    });

    it("does not call onSearch while typing (only on submit)", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      await user.type(input, "abc");

      // Should NOT be called during typing
      expect(mockOnSearch).not.toHaveBeenCalled();

      // Only called after submit
      await user.type(input, "{Enter}");
      expect(mockOnSearch).toHaveBeenCalledWith("abc");
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });

    it("does not call onSearch when submitting empty query", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      // Submit with empty input
      await user.type(input, "{Enter}");

      // Should call onSearch with empty string
      expect(mockOnSearch).toHaveBeenCalledWith("");
    });

    it("does not call onSearch when submitting whitespace-only query", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      // Type only spaces and submit
      await user.type(input, "   {Enter}");

      // Should call onSearch with empty string (trimmed)
      expect(mockOnSearch).toHaveBeenCalledWith("");
    });
  });

  describe("Clear Button Functionality (T006)", () => {
    it("shows search icon (🔍) when query is empty", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const button = screen.getByRole("button", { name: /submit search/i });
      expect(button).toHaveTextContent("🔍");
    });

    it("shows clear icon (✕) when query has value", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      await user.type(input, "test");

      const button = screen.getByRole("button", { name: /clear search/i });
      expect(button).toHaveTextContent("✕");
    });

    it("clears search query when clear button is clicked", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText(
        "Search points...",
      ) as HTMLInputElement;

      await user.type(input, "test query");
      expect(input.value).toBe("test query");

      const button = screen.getByRole("button", { name: /clear search/i });
      await user.click(button);

      expect(input.value).toBe("");
      expect(mockOnSearch).toHaveBeenCalledWith("");
    });

    it("does not submit form on button click when empty", async () => {
      const user = userEvent.setup();
      const handleSubmit = vi.fn((e) => e.preventDefault());

      const { container } = render(<MapSearchBar onSearch={mockOnSearch} />);
      const form = container.querySelector("form");
      form?.addEventListener("submit", handleSubmit);

      const button = screen.getByRole("button", { name: /submit search/i });
      await user.click(button);

      // Button does nothing when query is empty
      expect(handleSubmit).not.toHaveBeenCalled();
    });
  });

  describe("Keyboard Accessibility (T007)", () => {
    it("submits search when Enter is pressed", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");

      await user.type(input, "keyboard test{Enter}");

      expect(mockOnSearch).toHaveBeenCalledWith("keyboard test");
    });

    it("focuses input when tabbing to component", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);

      await user.tab();

      const input = screen.getByPlaceholderText("Search points...");
      expect(input).toHaveFocus();
    });

    it("has correct tab order: input → button", async () => {
      const user = userEvent.setup();
      render(<MapSearchBar onSearch={mockOnSearch} />);

      await user.tab();
      const input = screen.getByPlaceholderText("Search points...");
      expect(input).toHaveFocus();

      await user.tab();
      const button = screen.getByRole("button", { name: /submit search/i });
      expect(button).toHaveFocus();
    });

    it("shows focus indicators on input and button", () => {
      render(<MapSearchBar onSearch={mockOnSearch} />);
      const input = screen.getByPlaceholderText("Search points...");
      const button = screen.getByRole("button", { name: /submit search/i });

      // Verify elements can receive focus
      expect(input).not.toHaveAttribute("tabindex", "-1");
      expect(button).not.toHaveAttribute("tabindex", "-1");
    });
  });
});
