/**
 * Tests for PasswordChangeForm component.
 *
 * Tests password change form validation and submission.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../../src/test/test-utils";
import { PasswordChangeForm } from "../../../src/components/account/PasswordChangeForm";

// Mock hooks
const mockUpdatePassword = vi.fn();

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    updatePassword: mockUpdatePassword,
    isUpdating: false,
  }),
}));

describe("PasswordChangeForm Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render all password fields", () => {
    renderWithProviders(<PasswordChangeForm />);

    expect(screen.getByLabelText(/current password/i)).toBeTruthy();
    expect(screen.getByLabelText(/^new password/i)).toBeTruthy();
    expect(screen.getByLabelText(/confirm new password/i)).toBeTruthy();
  });

  it("should have submit button disabled when fields are empty", () => {
    renderWithProviders(<PasswordChangeForm />);

    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });
    expect((submitButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("should enable submit button when all fields are filled", () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);

    fireEvent.change(oldPassword, { target: { value: "old123456" } });
    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "new123456" } });

    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });
    expect((submitButton as HTMLButtonElement).disabled).toBe(false);
  });

  it("should show error when old password is missing", async () => {
    renderWithProviders(<PasswordChangeForm />);

    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "new123456" } });

    // Submit the form
    const form = submitButton.closest("form");
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe("Please enter your current password");
    });
  });

  it("should show error when new password is too short", async () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "old123456" } });
    fireEvent.change(newPassword, { target: { value: "short" } });
    fireEvent.change(confirmPassword, { target: { value: "short" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe(
        "New password must be at least 8 characters",
      );
    });
  });

  it("should show error when passwords do not match", async () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "old123456" } });
    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "different123" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe("New passwords do not match");
    });
  });

  it("should show error when new password is same as old", async () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "same123456" } });
    fireEvent.change(newPassword, { target: { value: "same123456" } });
    fireEvent.change(confirmPassword, { target: { value: "same123456" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe(
        "New password must be different from current password",
      );
    });
  });

  it("should submit form and show success message", async () => {
    mockUpdatePassword.mockResolvedValue({
      detail: "Password changed successfully",
    });

    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "old123456" } });
    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "new123456" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockUpdatePassword).toHaveBeenCalledWith({
        old_password: "old123456",
        new_password: "new123456",
      });
    });

    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Password changed successfully");
    });
  });

  it("should clear form after successful submission", async () => {
    mockUpdatePassword.mockResolvedValue({
      detail: "Success",
    });

    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(
      /current password/i,
    ) as HTMLInputElement;
    const newPassword = screen.getByLabelText(
      /^new password/i,
    ) as HTMLInputElement;
    const confirmPassword = screen.getByLabelText(
      /confirm new password/i,
    ) as HTMLInputElement;
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "old123456" } });
    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "new123456" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockUpdatePassword).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(oldPassword.value).toBe("");
      expect(newPassword.value).toBe("");
      expect(confirmPassword.value).toBe("");
    });
  });

  it("should toggle password visibility", () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const showCheckbox = screen.getByLabelText(/show passwords/i);

    // Initially hidden
    expect((oldPassword as HTMLInputElement).type).toBe("password");

    // Toggle to show
    fireEvent.click(showCheckbox);
    expect((oldPassword as HTMLInputElement).type).toBe("text");

    // Toggle back to hide
    fireEvent.click(showCheckbox);
    expect((oldPassword as HTMLInputElement).type).toBe("password");
  });

  it("should show error on failed submission", async () => {
    mockUpdatePassword.mockRejectedValue(new Error("Wrong password"));

    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    const newPassword = screen.getByLabelText(/^new password/i);
    const confirmPassword = screen.getByLabelText(/confirm new password/i);
    const submitButton = screen.getByRole("button", {
      name: /change password/i,
    });

    fireEvent.change(oldPassword, { target: { value: "wrong123456" } });
    fireEvent.change(newPassword, { target: { value: "new123456" } });
    fireEvent.change(confirmPassword, { target: { value: "new123456" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toContain("Failed to change password");
    });
  });

  it("should have accessible ARIA attributes", () => {
    renderWithProviders(<PasswordChangeForm />);

    const oldPassword = screen.getByLabelText(/current password/i);
    expect(oldPassword.getAttribute("aria-invalid")).toBe("false");
  });
});
