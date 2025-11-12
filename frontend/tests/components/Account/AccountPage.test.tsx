/**
 * Tests for AccountPage component.
 *
 * Tests account management page rendering and accessibility.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AccountPage } from "../../../src/pages/AccountPage";

// Mock hooks
vi.mock("../../../src/hooks/useAuth", () => ({
  useAuth: () => ({
    user: {
      id: "user-123",
      email: "test@example.com",
      pseudonym: "TestUser",
    },
    updateUser: vi.fn(),
  }),
}));

vi.mock("../../../src/hooks/useAccount", () => ({
  useAccount: () => ({
    account: {
      id: "user-123",
      email: "test@example.com",
      pseudonym: "TestUser",
    },
    fetchAccount: vi.fn(),
    updateAccountPseudonym: vi.fn(),
    requestEmailChange: vi.fn(),
    confirmEmailChange: vi.fn(),
    updatePassword: vi.fn(),
    requestAccountDeletion: vi.fn(),
    confirmAccountDeletion: vi.fn(),
    checkPseudonym: vi.fn(),
    clearError: vi.fn(),
    isLoading: false,
    isUpdating: false,
    isValidating: false,
    error: null,
  }),
}));

// Wrapper for router context
const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("AccountPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render all account management sections", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Check for main sections by headings (more specific)
    expect(
      screen.getByRole("heading", { name: /account management/i }),
    ).toBeTruthy();
    expect(screen.getByRole("heading", { name: /display name/i })).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: /change email address/i }),
    ).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: /change password/i }),
    ).toBeTruthy();
    expect(screen.getByRole("heading", { name: /danger zone/i })).toBeTruthy();
  });

  it("should display current user pseudonym", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    const pseudonymInput = screen.getByDisplayValue("TestUser");
    expect(pseudonymInput).toBeTruthy();
  });

  it("should have accessible heading structure", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    const headings = screen.getAllByRole("heading");
    expect(headings.length).toBeGreaterThan(0);

    // Main heading should be h1
    const mainHeading = screen.getByRole("heading", { level: 1 });
    expect(mainHeading.textContent).toMatch(/account/i);
  });

  it("should have accessible buttons", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);

    // All buttons should have accessible names
    buttons.forEach((button) => {
      expect(
        button.textContent || button.getAttribute("aria-label"),
      ).toBeTruthy();
    });
  });

  it("should organize content into sections", () => {
    const { container } = render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Check for section elements
    const sections = container.querySelectorAll("section");
    expect(sections.length).toBeGreaterThanOrEqual(3);
  });

  it("should render pseudonym field", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // PseudonymField should be present - use exact match for label
    const pseudonymInput = screen.getByLabelText("Pseudonym");
    expect(pseudonymInput).toBeTruthy();
  });

  it("should have proper semantic HTML structure", () => {
    const { container } = render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    // Check for main or container element
    const main =
      container.querySelector("main") ||
      container.querySelector(".account-page");
    expect(main).toBeTruthy();
  });

  it("should support keyboard navigation", () => {
    render(
      <RouterWrapper>
        <AccountPage />
      </RouterWrapper>,
    );

    const buttons = screen.getAllByRole("button");
    buttons.forEach((element) => {
      expect(element.getAttribute("tabindex")).not.toBe("-1");
    });
  });
});
