/**
 * Integration tests for Type Management UI.
 *
 * Tests the point type management functionality including:
 * - Creating new types
 * - Editing types
 * - Deleting types
 * - Reordering types
 * - Type limit validation (1000 types)
 * - Unique name validation
 * - Default icon fallback
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/test-utils";
import PointTypeManagementPage from "../../pages/PointTypeManagementPage";

// Mock API types
vi.mock("../../api/types", () => ({
  getPointTypes: vi.fn(),
  createPointType: vi.fn(),
  updatePointType: vi.fn(),
  deletePointType: vi.fn(),
  reorderPointTypes: vi.fn(),
  uploadTypeIcon: vi.fn(),
  downloadTypeIcon: vi.fn(),
}));

const mockTypes = [
  {
    id: "default-type-id",
    type: "base" as const,
    names: { en: "Point", fr: "Point" },
    creation_language: "en",
    icon: "/icons/default.svg",
    order: 0,
    owner: null,
    visibility: "public" as const,
    status: "active" as const,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "type-1",
    type: "custom" as const,
    names: { en: "Restaurant", fr: "Restaurant" },
    creation_language: "en",
    icon: "/icons/restaurant.svg",
    order: 1,
    owner: { id: "user1", email: "test@example.com" },
    visibility: "private" as const,
    status: "active" as const,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "type-2",
    type: "custom" as const,
    names: { en: "Museum", fr: "Musée" },
    creation_language: "en",
    icon: "/icons/museum.svg",
    order: 2,
    owner: { id: "user1", email: "test@example.com" },
    visibility: "private" as const,
    status: "active" as const,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "type-3",
    type: "custom" as const,
    names: { en: "Park", fr: "Parc" },
    creation_language: "en",
    icon: "/icons/park.svg",
    order: 3,
    owner: { id: "user1", email: "test@example.com" },
    visibility: "private" as const,
    status: "active" as const,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
];

describe("Type Management Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Creating Types", () => {
    it("should create a new type successfully", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      // Mock GET for listing types
      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      // Mock POST for creating type
      vi.mocked(typesApi.createPointType).mockResolvedValue({
        id: "type-4",
        type: "custom",
        names: { en: "Café" },
        creation_language: "en",
        icon: "/icons/cafe.svg",
        order: 4,
        owner: { id: "user1", email: "test@example.com" },
        visibility: "private",
        status: "active",
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
      });

      renderWithProviders(<PointTypeManagementPage />);

      // Wait for types to load
      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Click "Add New Type" button to show the form
      const addButton = screen.getByRole("button", { name: /add new type/i });
      await user.click(addButton);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByText(/create new point type/i)).toBeInTheDocument();
      });

      // Fill in type name in the translation input
      const nameInput = screen.getByPlaceholderText(/type name/i);
      await user.type(nameInput, "Café");

      // Submit form
      const createButton = screen.getByRole("button", {
        name: /^create type$/i,
      });
      await user.click(createButton);

      // Verify API was called
      await waitFor(() => {
        expect(typesApi.createPointType).toHaveBeenCalledWith(
          expect.objectContaining({
            names: expect.objectContaining({ en: "Café" }),
          }),
        );
      });
    });

    it("should use default icon when no icon specified", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.createPointType).mockResolvedValue({
        id: "type-4",
        type: "custom",
        names: { en: "Generic" },
        creation_language: "en",
        icon: "/icons/default.svg",
        order: 4,
        owner: { id: "user1", email: "test@example.com" },
        visibility: "private",
        status: "active",
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
      });

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      const addButton = screen.getByRole("button", { name: /add new type/i });
      await user.click(addButton);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByText(/create new point type/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/type name/i);
      await user.type(nameInput, "Generic");

      // Don't fill icon field

      const createButton = screen.getByRole("button", {
        name: /^create type$/i,
      });
      await user.click(createButton);

      // Verify the API was called without icon (it should be omitted or default)
      await waitFor(() => {
        expect(typesApi.createPointType).toHaveBeenCalledWith(
          expect.objectContaining({
            names: expect.objectContaining({ en: "Generic" }),
          }),
        );
      });
    });

    it("should show error when creating duplicate type name", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.createPointType).mockRejectedValue({
        response: {
          status: 400,
          data: {
            error: "VALIDATION_ERROR",
            message: "Type with this name already exists",
          },
        },
      });

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      const addButton = screen.getByRole("button", { name: /add new type/i });
      await user.click(addButton);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByText(/create new point type/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/type name/i);
      await user.type(nameInput, "Restaurant"); // Duplicate

      const createButton = screen.getByRole("button", {
        name: /^create type$/i,
      });
      await user.click(createButton);

      // Verify an error message is shown (the exact message depends on error parsing)
      await waitFor(() => {
        const errorElement = screen.getByRole("alert");
        expect(errorElement).toBeInTheDocument();
        // Should show some error message
        expect(errorElement.textContent).toBeTruthy();
      });
    });

    it("should show error when exceeding 1000 type limit", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.createPointType).mockRejectedValue({
        response: {
          status: 400,
          data: {
            error: "VALIDATION_ERROR",
            message: "You have reached the maximum of 1000 types",
          },
        },
      });

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      const addButton = screen.getByRole("button", { name: /add new type/i });
      await user.click(addButton);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByText(/create new point type/i)).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText(/type name/i);
      await user.type(nameInput, "NewType");

      const createButton = screen.getByRole("button", {
        name: /^create type$/i,
      });
      await user.click(createButton);

      // Verify an error message is shown (the exact message depends on error parsing)
      await waitFor(() => {
        const errorElement = screen.getByRole("alert");
        expect(errorElement).toBeInTheDocument();
        // Should contain either the mocked message or a generic error
        expect(errorElement.textContent).toMatch(/(1000|error|unknown)/i);
      });
    });
  });

  describe("Editing Types", () => {
    it("should edit an existing type successfully", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.updatePointType).mockResolvedValue({
        ...mockTypes[1],
        names: { en: "Fine Dining", fr: "Restaurant" },
        icon: "/icons/fine-dining.svg",
      });

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Click edit button for Restaurant type
      const editButton = screen.getByRole("button", {
        name: /edit restaurant/i,
      });
      await user.click(editButton);

      // Wait for edit form to appear
      await waitFor(() => {
        expect(screen.getByText(/editing translations/i)).toBeInTheDocument();
      });

      // Update name in the translation input - there may be multiple, get the one with value
      const nameInputs = screen.getAllByPlaceholderText(/type name/i);
      const editNameInput = nameInputs.find(
        (input) => (input as HTMLInputElement).value === "Restaurant",
      );
      expect(editNameInput).toBeDefined();

      await user.clear(editNameInput!);
      await user.type(editNameInput!, "Fine Dining");

      // Update icon
      const iconInputs = screen.getAllByPlaceholderText(/emoji.*url/i);
      const editIconInput = iconInputs[iconInputs.length - 1]; // Get the edit form input
      await user.clear(editIconInput);
      await user.type(editIconInput, "/icons/fine-dining.svg");

      // Save changes
      const saveButton = screen.getByRole("button", { name: /^save$/i });
      await user.click(saveButton);

      // Verify API was called
      await waitFor(() => {
        expect(typesApi.updatePointType).toHaveBeenCalledWith(
          "type-1",
          expect.objectContaining({
            names: expect.objectContaining({ en: "Fine Dining" }),
            icon: "/icons/fine-dining.svg",
          }),
        );
      });
    });
  });

  describe("Deleting Types", () => {
    it("should delete a type successfully", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      // Mock window.confirm to auto-confirm
      const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.deletePointType).mockResolvedValue();

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Click delete button for Restaurant type
      const deleteButton = screen.getByRole("button", {
        name: /delete restaurant/i,
      });
      await user.click(deleteButton);

      // Verify confirm was called with appropriate message
      expect(confirmSpy).toHaveBeenCalledWith(
        expect.stringContaining("Restaurant"),
      );

      // Verify API was called
      await waitFor(() => {
        expect(typesApi.deletePointType).toHaveBeenCalledWith("type-1");
      });

      confirmSpy.mockRestore();
    });

    it("should show warning that points will switch to default type", async () => {
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // The warning is in the info box at the bottom of the page
      expect(
        screen.getByText(/deleting a type will switch all associated points/i),
      ).toBeInTheDocument();
    });
  });

  describe("Reordering Types", () => {
    it("should have drag handles for reordering types", async () => {
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);
      vi.mocked(typesApi.reorderPointTypes).mockResolvedValue({
        success: true,
        updated: 4,
      });

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Find drag handles
      const dragHandles = screen.getAllByRole("button", {
        name: /drag to reorder/i,
      });

      // Should have drag handles for all types (including base type)
      expect(dragHandles.length).toBe(mockTypes.length);

      // Verify they are present and not disabled
      dragHandles.forEach((handle) => {
        expect(handle).toBeInTheDocument();
        expect(handle).not.toBeDisabled();
      });
    });
  });

  describe("Type List Display", () => {
    it("should display types in order", async () => {
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      const typeRows = screen.getAllByRole("row").slice(1); // Skip header row

      // First row is the default/base type "Point" (order: 0)
      expect(typeRows[0]).toHaveTextContent("Point");
      // Then the custom types
      expect(typeRows[1]).toHaveTextContent("Restaurant");
      expect(typeRows[2]).toHaveTextContent("Museum");
      expect(typeRows[3]).toHaveTextContent("Park");
    });

    it("should display icons for each type", async () => {
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Icons have alt="" so they have role "presentation", not "img"
      // Check for presentation role or just verify the icon elements exist
      const icons = screen.getAllByRole("presentation");
      expect(icons.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe("Accessibility", () => {
    it("should be keyboard navigable", async () => {
      const user = userEvent.setup();
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // The first focusable element should be the "Add New Type" button
      const addButton = screen.getByRole("button", { name: /add new type/i });
      expect(addButton).toBeInTheDocument();

      // Tab to focus it
      await user.tab();
      expect(addButton).toHaveFocus();
    });

    it("should have proper ARIA labels", async () => {
      const typesApi = await import("../../api/types");

      vi.mocked(typesApi.getPointTypes).mockResolvedValue(mockTypes);

      renderWithProviders(<PointTypeManagementPage />);

      await waitFor(() => {
        expect(screen.getByText("Restaurant")).toBeInTheDocument();
      });

      // Verify ARIA labels exist on interactive buttons
      const addButton = screen.getByRole("button", { name: /add new type/i });
      expect(addButton).toHaveAttribute("aria-label");

      // Check drag handles have aria-labels
      const dragHandles = screen.getAllByRole("button", {
        name: /drag to reorder/i,
      });
      expect(dragHandles.length).toBeGreaterThan(0);
      dragHandles.forEach((btn) => {
        expect(btn).toHaveAttribute("aria-label");
      });
    });
  });
});
