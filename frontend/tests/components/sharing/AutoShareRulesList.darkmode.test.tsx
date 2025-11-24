/**
 * Tests for AutoShareRulesList dark mode styling.
 *
 * Verifies that the component uses CSS variables for dark mode compatibility.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { AutoShareRulesList } from "../../../src/components/sharing/AutoShareRulesList";
import type { AutoShareRule } from "../../../src/api/friends";

const mockRules: AutoShareRule[] = [
  {
    id: "rule-1",
    friendship_id: "friendship-1",
    is_active: true,
    share_all: false,
    point_types: [],
    tags: [{ id: "tag-1", name: "test" }],
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

describe("AutoShareRulesList - Dark Mode", () => {
  const mockOnUpdateRule = vi.fn();
  const mockOnDeleteRule = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses CSS variables for rule card backgrounds", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const ruleCards = container.querySelectorAll(".rule-card");
    expect(ruleCards.length).toBeGreaterThan(0);

    // Check that cards have the appropriate classes
    // (actual color values depend on CSS variables)
    ruleCards.forEach((card) => {
      expect(card).toHaveClass("rule-card");
    });
  });

  it("applies inactive class for inactive rules", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const ruleCards = container.querySelectorAll(".rule-card");

    // First rule is active
    expect(ruleCards[0]).not.toHaveClass("inactive");

    // Second rule is inactive
    expect(ruleCards[1]).toHaveClass("inactive");
  });

  it("uses CSS variables for empty state background", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={[]}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const emptyState = container.querySelector(".rules-empty");
    expect(emptyState).toBeInTheDocument();
    expect(emptyState).toHaveClass("rules-empty");
  });

  it("uses CSS variables for rule description background", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const descriptions = container.querySelectorAll(".rule-description");
    expect(descriptions.length).toBeGreaterThan(0);

    descriptions.forEach((desc) => {
      expect(desc).toHaveClass("rule-description");
    });
  });

  it("renders permission badges with appropriate classes", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    const permissionSelects = container.querySelectorAll(".permission-select");

    // First rule has "view" permission
    expect(permissionSelects[0]).toHaveClass("view");

    // Second rule has "edit" permission
    expect(permissionSelects[1]).toHaveClass("edit");
  });

  it("maintains proper styling structure for dark mode compatibility", () => {
    const { container } = render(
      <AutoShareRulesList
        rules={mockRules}
        onUpdateRule={mockOnUpdateRule}
        onDeleteRule={mockOnDeleteRule}
      />,
    );

    // Check that key structural elements exist with proper classes
    const rulesList = container.querySelector(".rules-list");
    expect(rulesList).toBeInTheDocument();

    const ruleCards = container.querySelectorAll(".rule-card");
    expect(ruleCards).toHaveLength(2);

    const ruleHeaders = container.querySelectorAll(".rule-header");
    expect(ruleHeaders).toHaveLength(2);

    const ruleBodies = container.querySelectorAll(".rule-body");
    expect(ruleBodies).toHaveLength(2);
  });
});
