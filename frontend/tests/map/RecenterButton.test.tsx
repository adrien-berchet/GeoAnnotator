import "@testing-library/jest-dom";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RecenterButton } from "../../src/components/map/RecenterButton";

describe("RecenterButton", () => {
  it("invokes onClick when enabled", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<RecenterButton onClick={handleClick} />);

    const button = screen.getByRole("button", {
      name: /recenter on my location/i,
    });

    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("disables interactions when location is unavailable", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<RecenterButton onClick={handleClick} disabled />);

    const button = screen.getByRole("button", {
      name: /recenter on my location \(disabled\)/i,
    });

    expect(button).toBeDisabled();
    await user.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("uses the disabled modifier class for styling", () => {
    const { rerender } = render(<RecenterButton onClick={vi.fn()} />);

    let button = screen.getByRole("button", {
      name: /recenter on my location/i,
    });
    expect(button.className).not.toContain("disabled");

    rerender(<RecenterButton onClick={vi.fn()} disabled />);

    button = screen.getByRole("button", {
      name: /recenter on my location \(disabled\)/i,
    });
    expect(button.className).toContain("disabled");
  });
});
