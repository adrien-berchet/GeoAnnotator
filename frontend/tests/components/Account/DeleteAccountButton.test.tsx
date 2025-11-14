/**
 * Tests for DeleteAccountButton component.
 *
 * Tests delete account modal and confirmation flow.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../../src/test/test-utils";
import { DeleteAccountButton } from "../../../src/components/account/DeleteAccountButton";

// Mock hooks
const mockRequestAccountDeletion = vi.fn();

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    requestAccountDeletion: mockRequestAccountDeletion,
    isUpdating: false,
  }),
}));

describe("DeleteAccountButton Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Don't use fake timers globally - only where needed
  });

  afterEach(() => {
    // Clean up
  });

  it("should render delete button", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    expect(deleteButton).toBeTruthy();
  });

  it("should open modal when button is clicked", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    // Modal should be visible
    const modalHeading = screen.getByRole("heading", {
      name: /delete account/i,
    });
    expect(modalHeading).toBeTruthy();
  });

  it("should display username in warning", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    // Check for username in modal
    expect(screen.getByText(/TestUser/)).toBeTruthy();
  });

  it("should close modal when close button is clicked", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const closeButton = screen.getByRole("button", { name: /close modal/i });
    fireEvent.click(closeButton);

    // Modal should be closed
    expect(
      screen.queryByRole("heading", { name: /delete account/i }),
    ).toBeNull();
  });

  it("should close modal when cancel button is clicked", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Modal should be closed
    expect(
      screen.queryByRole("heading", { name: /delete account/i }),
    ).toBeNull();
  });

  it("should close modal when clicking overlay", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const overlay = document.querySelector(".modal-overlay");
    expect(overlay).toBeTruthy();

    fireEvent.click(overlay!);

    // Modal should be closed
    expect(
      screen.queryByRole("heading", { name: /delete account/i }),
    ).toBeNull();
  });

  it("should have confirm button disabled when text is wrong", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "wrong" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    expect((confirmButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("should enable confirm button when correct text is entered", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "DELETE" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    expect((confirmButton as HTMLButtonElement).disabled).toBe(false);
  });

  it("should disable button when wrong text is entered", async () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "wrong" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });

    // Button should be disabled with wrong text
    expect((confirmButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("should submit deletion request and show success", async () => {
    mockRequestAccountDeletion.mockResolvedValue({
      detail: "Deletion email sent",
    });

    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "DELETE" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockRequestAccountDeletion).toHaveBeenCalled();
    });

    await waitFor(() => {
      const success = screen.getByRole("status");
      expect(success.textContent).toContain("Confirmation email sent");
    });
  });

  it("should close modal after success with delay", async () => {
    mockRequestAccountDeletion.mockResolvedValue({
      detail: "Deletion email sent",
    });

    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "DELETE" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockRequestAccountDeletion).toHaveBeenCalled();
    });

    // Modal still visible immediately after
    expect(screen.getByRole("status")).toBeTruthy();

    // Wait for modal to close (3 second delay)
    await waitFor(
      () => {
        expect(
          screen.queryByRole("heading", { name: /delete account/i }),
        ).toBeNull();
      },
      { timeout: 4000 },
    ); // Allow 4s for 3s delay + buffer
  });

  it("should show error on failed submission", async () => {
    mockRequestAccountDeletion.mockRejectedValue(new Error("Network error"));

    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
    fireEvent.change(confirmInput, { target: { value: "DELETE" } });

    const confirmButton = screen.getByRole("button", {
      name: /send confirmation email/i,
    });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      const error = screen.getByRole("alert");
      expect(error.textContent).toContain(
        "Failed to send deletion confirmation",
      );
    });
  });

  it("should have accessible modal structure", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    // Check for accessible heading
    const heading = screen.getByRole("heading", { name: /delete account/i });
    expect(heading).toBeTruthy();

    // Check for close button with aria-label
    const closeButton = screen.getByRole("button", { name: /close modal/i });
    expect(closeButton.getAttribute("aria-label")).toBe("Close modal");
  });

  it("should prevent modal close when clicking inside content", () => {
    renderWithProviders(<DeleteAccountButton username="TestUser" />);

    const deleteButton = screen.getByRole("button", {
      name: /delete my account/i,
    });
    fireEvent.click(deleteButton);

    const modalContent = document.querySelector(".modal-content");
    expect(modalContent).toBeTruthy();

    fireEvent.click(modalContent!);

    // Modal should still be open
    expect(
      screen.getByRole("heading", { name: /delete account/i }),
    ).toBeTruthy();
  });
});
