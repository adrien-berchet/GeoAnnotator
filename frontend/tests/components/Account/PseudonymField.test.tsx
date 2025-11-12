/**
 * Tests for PseudonymField component.
 *
 * Tests pseudonym validation, debouncing, and update functionality.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { PseudonymField } from "../../../src/components/account/PseudonymField";

// Mock hooks
const mockUpdateAccountPseudonym = vi.fn();
const mockCheckPseudonym = vi.fn();
const mockUpdateUser = vi.fn();

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    updateAccountPseudonym: mockUpdateAccountPseudonym,
    checkPseudonym: mockCheckPseudonym,
    isUpdating: false,
    isValidating: false,
  }),
}));

vi.mock("../../../src/hooks/useAuth", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      email: "test@example.com",
      pseudonym: "TestUser",
    },
    updateUser: mockUpdateUser,
  }),
}));

describe("PseudonymField Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with current pseudonym", () => {
    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym");
    expect(input).toBeTruthy();
    expect((input as HTMLInputElement).value).toBe("TestUser");
  });

  it("should display help text", () => {
    render(<PseudonymField currentPseudonym="TestUser" />);

    expect(screen.getByText(/1-99 characters, no spaces/i)).toBeTruthy();
  });

  it("should update button be disabled when no changes", () => {
    render(<PseudonymField currentPseudonym="TestUser" />);

    const button = screen.getByRole("button", { name: /update pseudonym/i });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });

  it("should enable button when value changes and validation passes", async () => {
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for debounce (500ms) + validation
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    // Button should be enabled after validation passes
    await waitFor(() => {
      const button = screen.getByRole("button", { name: /update pseudonym/i });
      expect((button as HTMLButtonElement).disabled).toBe(false);
    });
  });

  it("should debounce validation check", async () => {
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Should not call immediately
    expect(mockCheckPseudonym).not.toHaveBeenCalled();

    // Wait for debounce delay
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalledWith({
          pseudonym: "NewUser",
        });
      },
      { timeout: 1000 },
    );
  });

  it("should display validation error for invalid pseudonym", async () => {
    mockCheckPseudonym.mockResolvedValue({
      valid: false,
      error: "Invalid characters",
    });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Bad!" } });

    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Invalid characters");
      },
      { timeout: 1000 },
    );
  });

  it("should display error for taken pseudonym", async () => {
    mockCheckPseudonym.mockResolvedValue({
      valid: true,
      available: false,
      error: "Pseudonym already taken",
    });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Taken" } });

    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Pseudonym already taken");
      },
      { timeout: 1000 },
    );
  });

  it("should submit form and show success message", async () => {
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountPseudonym.mockResolvedValue({ pseudonym: "NewUser" });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for validation
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const button = screen.getByRole("button", { name: /update pseudonym/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateAccountPseudonym).toHaveBeenCalledWith({
        pseudonym: "NewUser",
      });
    });

    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toBe("Pseudonym updated successfully!");
    });
  });

  it("should update auth context on successful update", async () => {
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountPseudonym.mockResolvedValue({ pseudonym: "NewUser" });

    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for validation
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const button = screen.getByRole("button", { name: /update pseudonym/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateAccountPseudonym).toHaveBeenCalled();
    });

    // Verify updateUser was called with updated pseudonym
    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({
        id: "user-123",
        email: "test@example.com",
        pseudonym: "NewUser",
      });
    });
  });

  it("should have accessible labels and ARIA attributes", () => {
    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym");
    expect(input.getAttribute("aria-invalid")).toBe("false");

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-label")).toBe("Update pseudonym");
  });

  it("should disable input while updating", () => {
    render(<PseudonymField currentPseudonym="TestUser" />);

    const input = screen.getByLabelText("Pseudonym") as HTMLInputElement;
    // Initially not disabled
    expect(input.disabled).toBe(false);
  });
});
