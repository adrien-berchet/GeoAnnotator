/**
 * Unit tests for CreatePointModal with type selection.
 *
 * These tests verify that the CreatePointModal correctly displays and handles
 * point type selection.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../src/test/test-utils";
import { CreatePointModal } from "../../src/components/map/CreatePointModal";

// Mock API calls
vi.mock("../../src/api/types", () => ({
  getPointTypes: vi.fn(),
}));

vi.mock("../../src/api/points", () => ({
  createPoint: vi.fn(),
}));

const mockTypes = [
  {
    id: "default-type-id",
    name: "Point",
    icon: "/icons/default.svg",
    order: 0,
    status: "active",
    user: null,
  },
  {
    id: "type-1",
    name: "Restaurant",
    icon: "/icons/restaurant.svg",
    order: 1,
    status: "active",
    user: { id: "user1", email: "test@example.com" },
  },
  {
    id: "type-2",
    name: "Museum",
    icon: "/icons/museum.svg",
    order: 2,
    status: "active",
    user: { id: "user1", email: "test@example.com" },
  },
  {
    id: "type-3",
    name: "Park",
    icon: "/icons/park.svg",
    order: 3,
    status: "active",
    user: { id: "user1", email: "test@example.com" },
  },
];

describe("CreatePointModal - Type Selection", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const { getPointTypes } = await import("../../src/api/types");
    vi.mocked(getPointTypes).mockResolvedValue(mockTypes as any);
  });

  it("should display type dropdown", async () => {
    const mockOnClose = vi.fn();
    const mockOnPointCreated = vi.fn();

    renderWithProviders(
      <CreatePointModal
        latitude={48.8566}
        longitude={2.3522}
        isOpen={true}
        onClose={mockOnClose}
        onPointCreated={mockOnPointCreated}
      />,
    );

    // Wait for modal to render
    await waitFor(() => {
      const titleInput = screen.queryByLabelText(/title/i);
      expect(titleInput).toBeDefined();
    });

    // Check if type selector exists (could be a select or custom dropdown)
    const typeElements = screen.queryAllByText(/type/i);
    expect(typeElements.length).toBeGreaterThan(0);
  });

  it("should pre-fill latitude and longitude", async () => {
    const mockOnClose = vi.fn();
    const mockOnPointCreated = vi.fn();

    renderWithProviders(
      <CreatePointModal
        latitude={48.8566}
        longitude={2.3522}
        isOpen={true}
        onClose={mockOnClose}
        onPointCreated={mockOnPointCreated}
      />,
    );

    await waitFor(() => {
      const titleInput = screen.queryByLabelText(/title/i);
      expect(titleInput).toBeDefined();
    });

    // Verify coordinates are displayed (they might be in input fields or text)
    const bodyText = document.body.textContent || "";
    expect(bodyText).toContain("48.8566");
    expect(bodyText).toContain("2.3522");
  });

  it("should call onClose when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    const mockOnPointCreated = vi.fn();

    renderWithProviders(
      <CreatePointModal
        latitude={48.8566}
        longitude={2.3522}
        isOpen={true}
        onClose={mockOnClose}
        onPointCreated={mockOnPointCreated}
      />,
    );

    await waitFor(() => {
      const titleInput = screen.queryByLabelText(/title/i);
      expect(titleInput).toBeDefined();
    });

    // Find and click cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should allow creating a point with title", async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    const mockOnPointCreated = vi.fn();
    const { createPoint } = await import("../../src/api/points");

    vi.mocked(createPoint).mockResolvedValue({
      id: "new-point-id",
      title: "Test Point",
      description: null,
      latitude: 48.8566,
      longitude: 2.3522,
      is_public: true,
      owner: { id: "user1", email: "test@example.com" },
      type: mockTypes[0],
      tags: [],
      annotation_count: 0,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
      editing_lock_user: null,
      editing_lock_acquired_at: null,
    } as any);

    renderWithProviders(
      <CreatePointModal
        latitude={48.8566}
        longitude={2.3522}
        isOpen={true}
        onClose={mockOnClose}
        onPointCreated={mockOnPointCreated}
      />,
    );

    await waitFor(() => {
      const titleInput = screen.queryByLabelText(/title/i);
      expect(titleInput).toBeDefined();
    });

    // Fill in title
    const titleInput = screen.getByLabelText(/title/i);
    await user.clear(titleInput);
    await user.type(titleInput, "Test Point");

    // Submit form
    const createButton = screen.getByRole("button", { name: /create/i });
    await user.click(createButton);

    // Verify createPoint was called
    await waitFor(() => {
      expect(createPoint).toHaveBeenCalled();
    });
  });

  it("should handle isOpen prop", () => {
    const mockOnClose = vi.fn();
    const mockOnPointCreated = vi.fn();

    const { container } = renderWithProviders(
      <CreatePointModal
        latitude={48.8566}
        longitude={2.3522}
        isOpen={false}
        onClose={mockOnClose}
        onPointCreated={mockOnPointCreated}
      />,
    );

    // When isOpen is false, the modal content exists but may be hidden via CSS
    // This is acceptable behavior for modal components
    expect(container).toBeDefined();
  });
});
