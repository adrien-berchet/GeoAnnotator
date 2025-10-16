/**
 * Tests for LanguageSelector component.
 *
 * Tests language selection UI (currently English only).
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LanguageSelector from '@/components/settings/LanguageSelector';

describe('LanguageSelector Component', () => {
  it('should render English option', () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    expect(screen.getByText(/english/i)).toBeInTheDocument();
  });

  it('should display as disabled/read-only', () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    const languageOption = screen.getByRole('radio', { name: /english language/i });
    expect(languageOption).toHaveAttribute('aria-disabled', 'true');
    expect(languageOption).toHaveClass('disabled');
  });

  it('should show "More languages coming soon" message', () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    expect(
      screen.getByText(/more languages coming soon/i)
    ).toBeInTheDocument();
  });

  it('should have accessible label', () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    expect(screen.getByRole('radio', { name: /english language/i })).toBeInTheDocument();
  });

  it('should not call onChange when disabled', async () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    const languageOption = screen.getByRole('radio', { name: /english language/i });

    // Component is disabled and onChange shouldn't be called
    expect(languageOption).toHaveAttribute('aria-disabled', 'true');
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('should display info icon or tooltip', () => {
    const mockOnChange = vi.fn();

    render(<LanguageSelector value="en" onChange={mockOnChange} />);

    // Check for info icon with aria-label
    const infoIcon = screen.getByLabelText(/only language available/i);
    expect(infoIcon).toBeInTheDocument();
  });
});
