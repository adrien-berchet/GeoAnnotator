/**
 * Tests for ExportSettings component.
 *
 * Tests export format selection UI with GeoJSON, KML, CSV options.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportSettings from '@/components/settings/ExportSettings';

describe('ExportSettings Component', () => {
  it('should render three export format options', () => {
    const mockOnChange = vi.fn();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    expect(screen.getByText(/geojson/i)).toBeInTheDocument();
    expect(screen.getByText(/kml/i)).toBeInTheDocument();
    expect(screen.getByText(/csv/i)).toBeInTheDocument();
  });

  it('should call onChange when format is selected', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    const kmlOption = screen.getByRole('radio', { name: /kml/i });
    await user.click(kmlOption);

    expect(mockOnChange).toHaveBeenCalledWith('kml');
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  it('should highlight selected value', () => {
    const mockOnChange = vi.fn();

    const { rerender } = render(
      <ExportSettings value="geojson" onChange={mockOnChange} />
    );

    const geojsonOption = screen.getByRole('radio', { name: /geojson/i });
    expect(geojsonOption).toBeChecked();

    // Rerender with different value
    rerender(<ExportSettings value="csv" onChange={mockOnChange} />);

    const csvOption = screen.getByRole('radio', { name: /csv/i });
    expect(csvOption).toBeChecked();
    expect(geojsonOption).not.toBeChecked();
  });

  it('should display description for each format', () => {
    const mockOnChange = vi.fn();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    // Each format should have a description
    expect(screen.getByText(/geographic data/i) || screen.getByText(/json/i)).toBeInTheDocument();
  });

  it('should have accessible labels', () => {
    const mockOnChange = vi.fn();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    expect(
      screen.getByLabelText(/export format/i) || screen.getByText(/default export format/i)
    ).toBeInTheDocument();
  });

  it('should update aria-checked attribute on selection', () => {
    const mockOnChange = vi.fn();

    render(<ExportSettings value="kml" onChange={mockOnChange} />);

    const kmlOption = screen.getByRole('radio', { name: /kml/i });
    expect(kmlOption).toHaveAttribute('aria-checked', 'true');
    expect(kmlOption).toBeChecked();

    const geojsonOption = screen.getByRole('radio', { name: /geojson/i });
    expect(geojsonOption).toHaveAttribute('aria-checked', 'false');
    expect(geojsonOption).not.toBeChecked();
  });

  it('should display format icons', () => {
    const mockOnChange = vi.fn();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    // Check that icons are present (they are emoji characters in the text content)
    const container = screen.getByRole('radiogroup');
    expect(container).toBeInTheDocument();

    // Verify all three format options are present with their emojis
    expect(screen.getByText('🗺️')).toBeInTheDocument(); // GeoJSON
    expect(screen.getByText('🌍')).toBeInTheDocument(); // KML
    expect(screen.getByText('📊')).toBeInTheDocument(); // CSV
  });

  it('should support all three format values', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    render(<ExportSettings value="geojson" onChange={mockOnChange} />);

    // Verify all three radio options exist
    expect(screen.getByRole('radio', { name: /geojson/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /kml/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /csv/i })).toBeInTheDocument();

    // Click KML (different from initial value)
    await user.click(screen.getByRole('radio', { name: /kml/i }));
    expect(mockOnChange).toHaveBeenCalledWith('kml');

    // Click CSV (different from previous)
    await user.click(screen.getByRole('radio', { name: /csv/i }));
    expect(mockOnChange).toHaveBeenCalledWith('csv');

    // Verify onChange was called twice
    expect(mockOnChange).toHaveBeenCalledTimes(2);
  });
});
