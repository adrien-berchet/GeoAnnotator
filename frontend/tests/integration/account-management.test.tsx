/**
 * Integration tests for account management workflows.
 *
 * Tests complete user journeys across account management features.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor, fireEvent, within } from "@testing-library/react";
import { renderWithProviders } from "../../src/test/test-utils";
import { AccountPage } from "../../src/pages/AccountPage";

// Mock hooks
const mockUpdateAccountUsername = vi.fn();
const mockCheckUsername = vi.fn();
const mockRequestEmailChange = vi.fn();
const mockUpdatePassword = vi.fn();
const mockRequestAccountDeletion = vi.fn();
const mockUpdateUser = vi.fn();

vi.mock("../../src/hooks/useAuth", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      email: "test@example.com",
      username: "TestUser",
    },
    updateUser: mockUpdateUser,
  }),
}));

vi.mock("../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    account: {
      id: "user-123",
      email: "test@example.com",
      username: "TestUser",
    },
    fetchAccount: vi.fn(),
    updateAccountUsername: mockUpdateAccountUsername,
    checkUsername: mockCheckUsername,
    requestEmailChange: mockRequestEmailChange,
    updatePassword: mockUpdatePassword,
    requestAccountDeletion: mockRequestAccountDeletion,
    clearError: vi.fn(),
    isLoading: false,
    isUpdating: false,
    isValidating: false,
    error: null,
  }),
}));

describe("Account Management Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Use real timers for integration tests
  });

  afterEach(() => {
    // Clean up
  });

  it("should complete full username update workflow", async () => {
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountUsername.mockResolvedValue({ username: "NewUser" });

    renderWithProviders(<AccountPage />);

    // Find username input
    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    expect(usernameInput.value).toBe("TestUser");

    // Change username
    fireEvent.change(usernameInput, { target: { value: "NewUser" } });

    // Wait for debounced validation (real timers, 500ms)
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalledWith({
          username: "NewUser",
        });
      },
      { timeout: 1000 },
    );

    // Submit form
    const updateButton = screen.getByRole("button", {
      name: /update username/i,
    });
    await waitFor(() => {
      expect((updateButton as HTMLButtonElement).disabled).toBe(false);
    });
    fireEvent.click(updateButton);

    // Verify submission
    await waitFor(() => {
      expect(mockUpdateAccountUsername).toHaveBeenCalledWith({
        username: "NewUser",
      });
    });

    // Verify auth context updated
    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith(
        expect.objectContaining({ username: "NewUser" }),
      );
    });

    // Verify success message
    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Username updated successfully");
    });
  }, 10000); // Increase timeout to 10s

  it("should complete email change request workflow", async () => {
    mockRequestEmailChange.mockResolvedValue({
      detail: "Confirmation email sent to new@example.com",
    });

    renderWithProviders(<AccountPage />);

    // Find email section
    const newEmailInput = screen.getByLabelText("New Email Address");

    // Enter new email
    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });

    // Submit
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(submitButton);

    // Verify request sent
    await waitFor(() => {
      expect(mockRequestEmailChange).toHaveBeenCalledWith({
        new_email: "new@example.com",
      });
    });

    // Verify success message
    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Confirmation email sent");
    });
  }, 10000);

  it("should complete password change workflow", async () => {
    mockUpdatePassword.mockResolvedValue({
      detail: "Password changed successfully",
    });

    renderWithProviders(<AccountPage />);

    // Find password fields
    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);

    // Fill form
    fireEvent.change(oldPassword, { target: { value: "oldPass123" } });
    fireEvent.change(newPassword, { target: { value: "newPass456" } });
    fireEvent.change(confirmPassword, { target: { value: "newPass456" } });

    // Submit
    const changeButton = screen.getByRole("button", {
      name: /change password/i,
    });
    fireEvent.click(changeButton);

    // Verify submission
    await waitFor(() => {
      expect(mockUpdatePassword).toHaveBeenCalledWith({
        old_password: "oldPass123",
        new_password: "newPass456",
      });
    });

    // Verify success
    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Password changed successfully");
    });
  }, 10000);

  it("should complete account deletion request workflow", async () => {
    mockRequestAccountDeletion.mockResolvedValue({
      detail: "Deletion confirmation email sent",
    });

    renderWithProviders(<AccountPage />);

    // Open delete modal
    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    // Verify modal opened
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /delete account/i }),
      ).toBeTruthy();
    });

    // Enter confirmation text
    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "DELETE" } });

    // Find modal and confirm deletion within it
    const modal = screen
      .getByRole("heading", { name: /delete account/i })
      .closest("div.modal-content") as HTMLElement;
    const confirmButton = within(modal).getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(confirmButton);

    // Verify request sent
    await waitFor(() => {
      expect(mockRequestAccountDeletion).toHaveBeenCalled();
    });

    // Verify success message
    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Confirmation email sent");
    });
  }, 10000);

  it("should handle multiple operations in sequence", async () => {
    // Setup mocks
    mockCheckUsername.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountUsername.mockResolvedValue({ username: "UpdatedUser" });
    mockRequestEmailChange.mockResolvedValue({
      detail: "Email sent",
    });

    renderWithProviders(<AccountPage />);

    // 1. Update username
    const usernameInput = screen.getByLabelText("Username");
    fireEvent.change(usernameInput, { target: { value: "UpdatedUser" } });

    // Wait for debounced validation
    await waitFor(
      () => {
        expect(mockCheckUsername).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const updateUsernameButton = screen.getByRole("button", {
      name: /update username/i,
    });
    fireEvent.click(updateUsernameButton);

    await waitFor(() => {
      expect(mockUpdateAccountUsername).toHaveBeenCalled();
    });

    // 2. Request email change
    const newEmailInput = screen.getByLabelText("New Email Address");
    fireEvent.change(newEmailInput, {
      target: { value: "updated@example.com" },
    });

    const emailButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(emailButton);

    await waitFor(() => {
      expect(mockRequestEmailChange).toHaveBeenCalledWith({
        new_email: "updated@example.com",
      });
    });

    // Verify both operations succeeded
    expect(mockUpdateAccountUsername).toHaveBeenCalledTimes(1);
    expect(mockRequestEmailChange).toHaveBeenCalledTimes(1);
  }, 10000);

  it("should display validation errors appropriately", async () => {
    mockCheckUsername.mockResolvedValue({
      valid: false,
      error: "Username contains invalid characters",
    });

    renderWithProviders(<AccountPage />);

    // Try invalid username
    const usernameInput = screen.getByLabelText("Username");
    fireEvent.change(usernameInput, { target: { value: "Bad Name!" } });

    // Wait for debounced validation
    // Should show validation error
    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Username contains invalid characters");
      },
      { timeout: 1000 },
    );

    // Update button should be disabled
    const updateButton = screen.getByRole("button", {
      name: /update username/i,
    });
    expect((updateButton as HTMLButtonElement).disabled).toBe(true);
  }, 10000);

  it("should handle accessibility navigation", () => {
    renderWithProviders(<AccountPage />);

    // Verify all sections have proper headings
    const mainHeading = screen.getByRole("heading", { level: 1 });
    expect(mainHeading.textContent).toMatch(/account/i);

    const sectionHeadings = screen.getAllByRole("heading", { level: 2 });
    expect(sectionHeadings.length).toBeGreaterThanOrEqual(4);

    // Verify all forms have labels
    const usernameInput = screen.getByLabelText("Username");
    const currentEmail = screen.getByLabelText("Current Email");
    const newEmail = screen.getByLabelText("New Email Address");
    const oldPassword = screen.getByLabelText(/current password/i);

    expect(usernameInput).toBeTruthy();
    expect(currentEmail).toBeTruthy();
    expect(newEmail).toBeTruthy();
    expect(oldPassword).toBeTruthy();
  });

  it("should display current user information correctly", () => {
    renderWithProviders(<AccountPage />);

    // Verify email is displayed
    expect(screen.getByText("test@example.com")).toBeTruthy();

    // Verify username in form (component still labeled "Username" in UI)
    const usernameInput = screen.getByLabelText("Username") as HTMLInputElement;
    expect(usernameInput.value).toBe("TestUser");

    // Verify current email in form
    const currentEmail = screen.getByLabelText(
      "Current Email",
    ) as HTMLInputElement;
    expect(currentEmail.value).toBe("test@example.com");
  });
});
