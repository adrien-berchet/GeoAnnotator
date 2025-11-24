/**
 * Tests for FriendDetailPage optimistic updates.
 *
 * Tests optimistic UI updates for auto-share rules.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../src/test/test-utils";
import { FriendDetailPage } from "../../src/pages/FriendDetailPage";
import * as friendsApi from "../../src/api/friends";

// Mock react-router
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ friendId: "friend-123" }),
    useNavigate: () => vi.fn(),
  };
});

const mockFriendDetail = {
  id: "user-456",
  username: "testfriend",
  friendship_id: "friend-123",
  friendship_created_at: "2024-01-01T00:00:00Z",
  shares_sent_count: 5,
  shares_received_count: 3,
  shared_points: [],
};

const mockAutoShareRules = [
  {
    id: "rule-1",
    friendship_id: "friend-123",
    is_active: true,
    share_all: false,
    point_types: [],
    tags: [{ id: "tag-1", name: "work" }],
    permission_level: "view" as const,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "rule-2",
    friendship_id: "friend-123",
    is_active: false,
    share_all: true,
    point_types: [],
    tags: [],
    permission_level: "edit" as const,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("FriendDetailPage - Optimistic Updates", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock API calls
    vi.spyOn(friendsApi, "getFriendDetail").mockResolvedValue(mockFriendDetail);
    vi.spyOn(friendsApi, "getAutoShareRules").mockResolvedValue(
      mockAutoShareRules,
    );
    vi.spyOn(friendsApi, "updateAutoShareRule").mockResolvedValue(
      mockAutoShareRules[0],
    );
  });

  it("updates rule status optimistically without flickering", async () => {
    const user = userEvent.setup();

    renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const toggles = screen.getAllByRole("checkbox");
    const firstToggle = toggles[0];

    // Initial state: active (checked)
    expect(firstToggle).toBeChecked();

    // Click to toggle
    await user.click(firstToggle);

    // Should update immediately (optimistic)
    expect(firstToggle).not.toBeChecked();

    // API should have been called
    await waitFor(() => {
      expect(friendsApi.updateAutoShareRule).toHaveBeenCalledWith(
        "friend-123",
        "rule-1",
        { is_active: false },
      );
    });

    // Should still be unchecked (no reload happened)
    expect(firstToggle).not.toBeChecked();
  });

  it("updates permission optimistically", async () => {
    const user = userEvent.setup();

    renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const permissionSelects = screen.getAllByRole("combobox");
    const firstSelect = permissionSelects[0];

    // Initial state: view
    expect(firstSelect).toHaveValue("view");

    // Change to edit
    await user.selectOptions(firstSelect, "edit");

    // Should update immediately (optimistic)
    expect(firstSelect).toHaveValue("edit");

    // API should have been called
    await waitFor(() => {
      expect(friendsApi.updateAutoShareRule).toHaveBeenCalledWith(
        "friend-123",
        "rule-1",
        { permission_level: "edit" },
      );
    });

    // Should still be edit (no reload happened)
    expect(firstSelect).toHaveValue("edit");
  });

  it("reverts optimistic update on API failure", async () => {
    const user = userEvent.setup();

    let rejectUpdate: (error: Error) => void;
    const updatePromise = new Promise<never>((_, reject) => {
      rejectUpdate = reject;
    });

    vi.spyOn(friendsApi, "updateAutoShareRule").mockReturnValueOnce(
      updatePromise,
    );

    renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const toggles = screen.getAllByRole("checkbox");
    const firstToggle = toggles[0];

    // Initial state: active (checked)
    expect(firstToggle).toBeChecked();

    // Click to toggle
    await user.click(firstToggle);

    // Should update immediately (optimistic)
    await waitFor(() => {
      expect(firstToggle).not.toBeChecked();
    });

    // Now trigger the API failure
    rejectUpdate!(new Error("Network error"));

    // Wait for error message
    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update rule status/),
      ).toBeInTheDocument();
    });

    // Should revert to original state (checked)
    await waitFor(() => {
      expect(firstToggle).toBeChecked();
    });
  });

  it("shows error message on update failure", async () => {
    const user = userEvent.setup();

    // Mock API failure
    vi.spyOn(friendsApi, "updateAutoShareRule").mockRejectedValueOnce(
      new Error("Permission denied"),
    );

    renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const permissionSelects = screen.getAllByRole("combobox");
    await user.selectOptions(permissionSelects[0], "manage");

    // Should show error message
    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update permission.*Permission denied/),
      ).toBeInTheDocument();
    });
  });

  it("does not reload rules on successful update", async () => {
    const user = userEvent.setup();
    const getAutoShareRulesSpy = vi.spyOn(friendsApi, "getAutoShareRules");

    renderWithProviders(<FriendDetailPage />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    // Clear the spy after initial load
    getAutoShareRulesSpy.mockClear();

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    // Wait for update to complete
    await waitFor(() => {
      expect(friendsApi.updateAutoShareRule).toHaveBeenCalled();
    });

    // Should NOT have called getAutoShareRules again (no reload)
    expect(getAutoShareRulesSpy).not.toHaveBeenCalled();
  });

  it("reloads rules only on API failure", async () => {
    const user = userEvent.setup();
    const getAutoShareRulesSpy = vi.spyOn(friendsApi, "getAutoShareRules");

    // Mock API failure
    vi.spyOn(friendsApi, "updateAutoShareRule").mockRejectedValueOnce(
      new Error("Network error"),
    );

    renderWithProviders(<FriendDetailPage />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    // Clear the spy after initial load
    getAutoShareRulesSpy.mockClear();

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    // Wait for error to appear and reload to happen
    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update rule status/),
      ).toBeInTheDocument();
    });

    // Should have reloaded rules to revert optimistic update
    expect(getAutoShareRulesSpy).toHaveBeenCalledTimes(1);
  });

  it("maintains UI state during multiple rapid updates", async () => {
    const user = userEvent.setup();

    renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const toggles = screen.getAllByRole("checkbox");
    const firstToggle = toggles[0];

    // Rapid clicks
    await user.click(firstToggle);
    await user.click(firstToggle);
    await user.click(firstToggle);

    // Should handle all updates
    await waitFor(() => {
      expect(friendsApi.updateAutoShareRule).toHaveBeenCalledTimes(3);
    });
  });

  it("keeps inactive class updated optimistically", async () => {
    const user = userEvent.setup();

    const { container } = renderWithProviders(<FriendDetailPage />);

    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText("Tags: work")).toBeInTheDocument();
    });

    const ruleCards = container.querySelectorAll(".rule-card");
    const firstCard = ruleCards[0];

    // Initial state: active (no inactive class)
    expect(firstCard).not.toHaveClass("inactive");

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    // Should add inactive class immediately
    await waitFor(() => {
      expect(firstCard).toHaveClass("inactive");
    });
  });
});
