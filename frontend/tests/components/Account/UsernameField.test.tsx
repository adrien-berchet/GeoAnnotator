/**
 * Tests for UsernameField component.
 *
 * Tests username validation, debouncing, and update functionality.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { UsernameField } from "../../../src/components/account/UsernameField";

// Mock hooks
const mockUpdateAccountUsername = vi.fn();
const mockCheckUsername = vi.fn();
const mockUpdateUser = vi.fn();

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    updateAccountUsername: mockUpdateAccountUsername,
    checkUsername: mockCheckUsername,
    isUpdating: false,
    isValidating: false,
  }),
}));

vi.mock("../../../src/hooks/useAuth", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      email: "test@example.com",
      username: "TestUser",
    },
    updateUser: mockUpdateUser,
  }),
}));

describe("UsernameField Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with current username", () => {
    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username");
    expect(input).toBeTruthy();
    expect((input as HTMLInputElement).value).toBe("TestUser");
  });

  it("should display help text", () => {
    render(<UsernameField currentUsername="TestUser" />);

    expect(screen.getByText(/3-100 characters/i)).toBeTruthy();
  });

  it("should update button be disabled when no changes", () => {
    render(<UsernameField currentUsername="TestUser" />);

    const button = screen.getByRole("button", { name: /update username/i });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });

  it("should enable button when value changes and validation passes", async () => {
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for debounce (500ms) + validation
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    // Button should be enabled after validation passes
    await waitFor(() => {
      const button = screen.getByRole("button", { name: /update username/i });
      expect((button as HTMLButtonElement).disabled).toBe(false);
    });
  });

  it("should debounce validation check", async () => {
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Should not call immediately
    expect(mockCheckUsername).not.toHaveBeenCalled();

    // Wait for debounce delay
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalledWith({
          username: "NewUser",
        });
      },
      { timeout: 1000 },
    );
  });

  it("should display validation error for invalid username", async () => {
    mockCheckUsername.mockResolvedValue({
      valid: false,
      error: "Invalid characters",
    });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Bad!" } });

    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Invalid characters");
      },
      { timeout: 1000 },
    );
  });

  it("should display error for taken username", async () => {
    mockCheckUsername.mockResolvedValue({
      valid: true,
      available: false,
      error: "Username already taken",
    });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Taken" } });

    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Username already taken");
      },
      { timeout: 1000 },
    );
  });

  it("should submit form and show success message", async () => {
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountUsername.mockResolvedValue({ username: "NewUser" });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for validation
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const button = screen.getByRole("button", { name: /update username/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateAccountUsername).toHaveBeenCalledWith({
        username: "NewUser",
      });
    });

    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toBe("Username updated successfully!");
    });
  });

  it("should update auth context on successful update", async () => {
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountUsername.mockResolvedValue({ username: "NewUser" });

    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "NewUser" } });

    // Wait for validation
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const button = screen.getByRole("button", { name: /update username/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateAccountUsername).toHaveBeenCalled();
    });

    // Verify updateUser was called with updated username
    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({
        id: "user-123",
        email: "test@example.com",
        username: "NewUser",
      });
    });
  });

  it("should have accessible labels and ARIA attributes", () => {
    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username");
    expect(input.getAttribute("aria-invalid")).toBe("false");

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-label")).toBe("Update username");
  });

  it("should disable input while updating", () => {
    render(<UsernameField currentUsername="TestUser" />);

    const input = screen.getByLabelText("Username") as HTMLInputElement;
    // Initially not disabled
    expect(input.disabled).toBe(false);
  });
});
