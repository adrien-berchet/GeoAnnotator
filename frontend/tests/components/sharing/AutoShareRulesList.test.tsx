/**
 * Tests for AutoShareRulesList component.
 *
 * Tests auto-share rules list rendering, interactions, and error handling.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AutoShareRulesList } from "../../../src/components/sharing/AutoShareRulesList";
import type { AutoShareRule } from "../../../src/api/friends";

const mockRules: AutoShareRule[] = [
  {
    id: "rule-1",
    friendship_id: "friendship-1",
    is_active: true,
    share_all: false,
    point_types: [
      {
        id: "type-1",
        names: { en: "Restaurant", fr: "Restaurant" },
        icon: "🍽️",
      },
    ],
    tags: [{ id: "tag-1", name: "favorite" }],
    permission_level: "view",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "rule-2",
    friendship_id: "friendship-1",
    is_active: false,
    share_all: true,
    point_types: [],
    tags: [],
    permission_level: "edit",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("AutoShareRulesList Component", () => {
  const mockOnUpdateRule = vi.fn();
  const mockOnDeleteRule = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnUpdateRule.mockResolvedValue(undefined);
    mockOnDeleteRule.mockResolvedValue(undefined);
  });

  it("renders empty state when no rules", () => {
    render(
      <AutoShareRulesList
        rules={[]}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    expect(screen.getByText("No auto-share rules yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Create a rule to automatically share/i),
    ).toBeInTheDocument();
  });

  it("renders list of rules", () => {
    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    expect(
      screen.getByText("Types: Restaurant + Tags: favorite"),
    ).toBeInTheDocument();
    expect(screen.getByText("All new points")).toBeInTheDocument();
  });

  it("displays active and inactive rules correctly", () => {
    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const activeStatus = screen.getAllByText("Active");
    const inactiveStatus = screen.getAllByText("Inactive");

    expect(activeStatus).toHaveLength(1);
    expect(inactiveStatus).toHaveLength(1);
  });

  it("toggles rule active status", async () => {
    const user = userEvent.setup();

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    await waitFor(() => {
      expect(mockOnUpdateRule).toHaveBeenCalledWith("rule-1", {
        is_active: false,
      });
    });
  });

  it("changes permission level", async () => {
    const user = userEvent.setup();

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const permissionSelects = screen.getAllByRole("combobox");
    await user.selectOptions(permissionSelects[0], "edit");

    await waitFor(() => {
      expect(mockOnUpdateRule).toHaveBeenCalledWith("rule-1", {
        permission_level: "edit",
      });
    });
  });

  it("does not update permission if same value selected", async () => {
    const user = userEvent.setup();

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const permissionSelects = screen.getAllByRole("combobox");
    await user.selectOptions(permissionSelects[0], "view");

    // Should not call update if already "view"
    expect(mockOnUpdateRule).not.toHaveBeenCalled();
  });

  it("deletes rule after confirmation", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const deleteButtons = screen.getAllByTitle("Delete rule");
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith(
        "Are you sure you want to delete this auto-share rule?",
      );
      expect(mockOnDeleteRule).toHaveBeenCalledWith("rule-1");
    });

    confirmSpy.mockRestore();
  });

  it("does not delete rule if not confirmed", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const deleteButtons = screen.getAllByTitle("Delete rule");
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalled();
    });

    expect(mockOnDeleteRule).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it("displays error message when update fails", async () => {
    const user = userEvent.setup();
    mockOnUpdateRule.mockRejectedValueOnce(new Error("Network error"));

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update rule status.*Network error/),
      ).toBeInTheDocument();
    });
  });

  it("displays error message when permission change fails", async () => {
    const user = userEvent.setup();
    mockOnUpdateRule.mockRejectedValueOnce(new Error("Permission denied"));

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const permissionSelects = screen.getAllByRole("combobox");
    await user.selectOptions(permissionSelects[0], "manage");

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to update permission.*Permission denied/),
      ).toBeInTheDocument();
    });
  });

  it("displays error message when delete fails", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    mockOnDeleteRule.mockRejectedValueOnce(new Error("Delete failed"));

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const deleteButtons = screen.getAllByTitle("Delete rule");
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to delete rule.*Delete failed/),
      ).toBeInTheDocument();
    });

    confirmSpy.mockRestore();
  });

  it("disables controls while updating", async () => {
    const user = userEvent.setup();
    let resolveUpdate: () => void;
    const updatePromise = new Promise<void>((resolve) => {
      resolveUpdate = resolve;
    });
    mockOnUpdateRule.mockReturnValue(updatePromise);

    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const toggles = screen.getAllByRole("checkbox");
    await user.click(toggles[0]);

    // Controls should be disabled
    expect(toggles[0]).toBeDisabled();
    const deleteButtons = screen.getAllByTitle("Delete rule");
    expect(deleteButtons[0]).toBeDisabled();

    // Resolve and check re-enabled
    resolveUpdate!();
    await waitFor(() => {
      expect(toggles[0]).not.toBeDisabled();
      expect(deleteButtons[0]).not.toBeDisabled();
    });
  });

  it("shows 'Share All' badge for share_all rules", () => {
    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const badges = screen.getAllByText("Share All");
    expect(badges).toHaveLength(1);
  });

  it("displays correct permission colors", () => {
    render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const permissionSelects = screen.getAllByRole("combobox");
    expect(permissionSelects[0]).toHaveClass("view");
    expect(permissionSelects[1]).toHaveClass("edit");
  });

  it("applies inactive class to inactive rules", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const ruleCards = container.querySelectorAll(".rule-card");
    expect(ruleCards[0]).not.toHaveClass("inactive");
    expect(ruleCards[1]).toHaveClass("inactive");
  });
});
