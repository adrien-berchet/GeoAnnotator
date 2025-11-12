/**
 * Tests for EmailChangeForm component.
 *
 * Tests email change form validation and submission.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { EmailChangeForm } from "../../../src/components/account/EmailChangeForm";

// Mock hooks
const mockRequestEmailChange = vi.fn();

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    requestEmailChange: mockRequestEmailChange,
    isUpdating: false,
  }),
}));

describe("EmailChangeForm Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with current email disabled", () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const currentEmailInput = screen.getByLabelText(
      "Current Email",
    ) as HTMLInputElement;
    expect(currentEmailInput.value).toBe("test@example.com");
    expect(currentEmailInput.disabled).toBe(true);
  });

  it("should have submit button disabled when new email is empty", () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    expect((submitButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("should enable submit button when new email is entered", () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });

    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    expect((submitButton as HTMLButtonElement).disabled).toBe(false);
  });

  it("should show error when email is same as current", async () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    fireEvent.change(newEmailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe(
        "New email must be different from current email",
      );
    });
  });

  it("should show error when email is invalid", async () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    fireEvent.change(newEmailInput, { target: { value: "invalid-email" } });

    // Submit the form
    const form = submitButton.closest("form");
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toBe("Please enter a valid email address");
    });
  });

  it("should submit form and show success message", async () => {
    mockRequestEmailChange.mockResolvedValue({
      detail: "Check your email for confirmation",
    });

    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRequestEmailChange).toHaveBeenCalledWith({
        new_email: "new@example.com",
      });
    });

    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Confirmation email sent");
    });
  });

  it("should clear form after successful submission", async () => {
    mockRequestEmailChange.mockResolvedValue({
      detail: "Check your email",
    });

    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText(
      "New Email Address",
    ) as HTMLInputElement;
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRequestEmailChange).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(newEmailInput.value).toBe("");
    });
  });

  it("should show error on failed submission", async () => {
    mockRequestEmailChange.mockRejectedValue(new Error("Network error"));

    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toContain("Failed to send confirmation email");
    });
  });

  it("should have accessible labels and ARIA attributes", () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const currentEmailInput = screen.getByLabelText("Current Email");
    const newEmailInput = screen.getByLabelText("New Email Address");

    expect(currentEmailInput.getAttribute("aria-label")).toBe(
      "Current email address",
    );
    expect(newEmailInput.getAttribute("aria-invalid")).toBe("false");
  });

  it("should clear error when typing in input", async () => {
    render(<EmailChangeForm currentEmail="test@example.com" />);

    const newEmailInput = screen.getByLabelText("New Email Address");
    const submitButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    // Trigger error
    fireEvent.change(newEmailInput, { target: { value: "test@example.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });

    // Type new value - error should clear
    fireEvent.change(newEmailInput, { target: { value: "new@example.com" } });

    expect(screen.queryByRole("alert")).toBeNull();
  });
});
