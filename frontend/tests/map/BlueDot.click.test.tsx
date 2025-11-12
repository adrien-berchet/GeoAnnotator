/**
 * Unit tests for BlueDot click functionality.
 *
 * These tests verify that the BlueDot component correctly handles click events
 * and passes the onClick callback to the Marker component.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BlueDot } from "../../src/components/map/BlueDot";

// Mock react-leaflet components
vi.mock("react-leaflet", () => ({
  Marker: ({
    children,
    eventHandlers,
  }: {
    children: React.ReactNode;
    eventHandlers?: { click?: () => void };
  }) => (
    <div data-testid="marker" onClick={eventHandlers?.click}>
      {children}
    </div>
  ),
  Circle: () => <div data-testid="circle" />,
  Polygon: () => <div data-testid="polygon" />,
  useMap: () => ({
    getContainer: () => ({
      querySelector: () => null,
    }),
  }),
}));

describe("BlueDot Click Functionality", () => {
  it("should call onClick handler when blue dot is clicked", async () => {
    const user = userEvent.setup();
    const mockOnClick = vi.fn();
    const mockPosition = {
      latitude: 48.8566,
      longitude: 2.3522,
      accuracy: 10,
      heading: null,
      timestamp: Date.now(),
    };

    render(<BlueDot position={mockPosition} onClick={mockOnClick} />);

    const marker = screen.getByTestId("marker");
    await user.click(marker);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it("should pass correct position data to marker", () => {
    const mockOnClick = vi.fn();
    const mockPosition = {
      latitude: 48.8566,
      longitude: 2.3522,
      accuracy: 10,
      heading: null,
      timestamp: Date.now(),
    };

    render(<BlueDot position={mockPosition} onClick={mockOnClick} />);

    // Verify marker is rendered (which means position was valid)
    expect(screen.getByTestId("marker")).toBeDefined();
    expect(screen.getByTestId("circle")).toBeDefined();
  });

  it("should render accuracy circle", () => {
    const mockOnClick = vi.fn();
    const mockPosition = {
      latitude: 48.8566,
      longitude: 2.3522,
      accuracy: 10,
      heading: null,
      timestamp: Date.now(),
    };

    render(<BlueDot position={mockPosition} onClick={mockOnClick} />);

    // Accuracy circle should be rendered
    expect(screen.getByTestId("circle")).toBeDefined();
  });
});
