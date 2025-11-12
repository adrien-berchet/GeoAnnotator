/**
 * Integration tests for account management workflows.
 *
 * Tests complete user journeys across account management features.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  waitFor,
  fireEvent,
  within,
} from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AccountPage } from "../../src/pages/AccountPage";

// Mock hooks
const mockUpdateAccountPseudonym = vi.fn();
const mockCheckPseudonym = vi.fn();
const mockRequestEmailChange = vi.fn();
const mockUpdatePassword = vi.fn();
const mockRequestAccountDeletion = vi.fn();
const mockUpdateUser = vi.fn();

vi.mock("../../src/hooks/useAuth", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      email: "test@example.com",
      pseudonym: "TestUser",
    },
    updateUser: mockUpdateUser,
  }),
}));

vi.mock("../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    account: {
      id: "user-123",
      email: "test@example.com",
      pseudonym: "TestUser",
    },
    fetchAccount: vi.fn(),
    updateAccountPseudonym: mockUpdateAccountPseudonym,
    checkPseudonym: mockCheckPseudonym,
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

const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("Account Management Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Use real timers for integration tests
  });

  afterEach(() => {
    // Clean up
  });

  it("should complete full pseudonym update workflow", async () => {
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountPseudonym.mockResolvedValue({ pseudonym: "NewUser" });

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Find pseudonym input
    const pseudonymInput = screen.getByLabelText(
      "Pseudonym",
    ) as HTMLInputElement;
    expect(pseudonymInput.value).toBe("TestUser");

    // Change pseudonym
    fireEvent.change(pseudonymInput, { target: { value: "NewUser" } });

    // Wait for debounced validation (real timers, 500ms)
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalledWith({
          pseudonym: "NewUser",
        });
      },
      { timeout: 1000 },
    );

    // Submit form
    const updateButton = screen.getByRole("button", {
      name: /update pseudonym/i,
    });
    await waitFor(() => {
      expect((updateButton as HTMLButtonElement).disabled).toBe(false);
    });
    fireEvent.click(updateButton);

    // Verify submission
    await waitFor(() => {
      expect(mockUpdateAccountPseudonym).toHaveBeenCalledWith({
        pseudonym: "NewUser",
      });
    });

    // Verify auth context updated
    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith(
        expect.objectContaining({ pseudonym: "NewUser" }),
      );
    });

    // Verify success message
    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Pseudonym updated successfully");
    });
  }, 10000); // Increase timeout to 10s

  it("should complete email change request workflow", async () => {
    mockRequestEmailChange.mockResolvedValue({
      detail: "Confirmation email sent to new@example.com",
    });

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

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

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

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

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

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
    mockCheckPseudonym.mockResolvedValue({ valid: true, available: true });
    mockUpdateAccountPseudonym.mockResolvedValue({ pseudonym: "UpdatedUser" });
    mockRequestEmailChange.mockResolvedValue({
      detail: "Email sent",
    });

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // 1. Update pseudonym
    const pseudonymInput = screen.getByLabelText("Pseudonym");
    fireEvent.change(pseudonymInput, { target: { value: "UpdatedUser" } });

    // Wait for debounced validation
    await waitFor(
      () => {
        expect(mockCheckPseudonym).toHaveBeenCalled();
      },
      { timeout: 1000 },
    );

    const updatePseudonymButton = screen.getByRole("button", {
      name: /update pseudonym/i,
    });
    fireEvent.click(updatePseudonymButton);

    await waitFor(() => {
      expect(mockUpdateAccountPseudonym).toHaveBeenCalled();
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
    expect(mockUpdateAccountPseudonym).toHaveBeenCalledTimes(1);
    expect(mockRequestEmailChange).toHaveBeenCalledTimes(1);
  }, 10000);

  it("should display validation errors appropriately", async () => {
    mockCheckPseudonym.mockResolvedValue({
      valid: false,
      error: "Pseudonym contains invalid characters",
    });

    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Try invalid pseudonym
    const pseudonymInput = screen.getByLabelText("Pseudonym");
    fireEvent.change(pseudonymInput, { target: { value: "Bad Name!" } });

    // Wait for debounced validation
    // Should show validation error
    await waitFor(
      () => {
        const error = screen.getByRole("alert");
        expect(error.textContent).toBe("Pseudonym contains invalid characters");
      },
      { timeout: 1000 },
    );

    // Update button should be disabled
    const updateButton = screen.getByRole("button", {
      name: /update pseudonym/i,
    });
    expect((updateButton as HTMLButtonElement).disabled).toBe(true);
  }, 10000);

  it("should handle accessibility navigation", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Verify all sections have proper headings
    const mainHeading = screen.getByRole("heading", { level: 1 });
    expect(mainHeading.textContent).toMatch(/account/i);

    const sectionHeadings = screen.getAllByRole("heading", { level: 2 });
    expect(sectionHeadings.length).toBeGreaterThanOrEqual(4);

    // Verify all forms have labels
    const pseudonymInput = screen.getByLabelText("Pseudonym");
    const currentEmail = screen.getByLabelText("Current Email");
    const newEmail = screen.getByLabelText("New Email Address");
    const oldPassword = screen.getByLabelText(/current password/i);

    expect(pseudonymInput).toBeTruthy();
    expect(currentEmail).toBeTruthy();
    expect(newEmail).toBeTruthy();
    expect(oldPassword).toBeTruthy();
  });

  it("should display current user information correctly", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Verify account info section
    expect(screen.getByText("user-123")).toBeTruthy();
    expect(screen.getByText("test@example.com")).toBeTruthy();

    // Verify pseudonym in form
    const pseudonymInput = screen.getByLabelText(
      "Pseudonym",
    ) as HTMLInputElement;
    expect(pseudonymInput.value).toBe("TestUser");

    // Verify current email in form
    const currentEmail = screen.getByLabelText(
      "Current Email",
    ) as HTMLInputElement;
    expect(currentEmail.value).toBe("test@example.com");
  });
});
