/**
 * Tests for LanguageSelector component.
 *
 * Tests language selection UI (English and French).
 */
import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import LanguageSelector from '@/components/settings/LanguageSelector';

describe('LanguageSelector Component', () => {
  it('should render English and French options', () => {
    const mockOnChange = vi.fn();

    renderWithProviders(<LanguageSelector value="en" onChange={mockOnChange} />);

    expect(screen.getByText(/english/i)).toBeInTheDocument();
    expect(screen.getByText(/french/i)).toBeInTheDocument();
  });

  it('should highlight selected language', () => {
    const mockOnChange = vi.fn();

    renderWithProviders(<LanguageSelector value="en" onChange={mockOnChange} />);

    const englishOption = screen.getByRole('radio', { name: /english language/i });
    expect(englishOption).toHaveAttribute('aria-checked', 'true');

    const frenchOption = screen.getByRole('radio', { name: /french language/i });
    expect(frenchOption).toHaveAttribute('aria-checked', 'false');
  });

  it('should call onChange when different language is selected', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<LanguageSelector value="en" onChange={mockOnChange} />);

    const frenchOption = screen.getByRole('radio', { name: /french language/i });
    await user.click(frenchOption);

    expect(mockOnChange).toHaveBeenCalledWith('fr');
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  it('should have accessible labels', () => {
    const mockOnChange = vi.fn();

    renderWithProviders(<LanguageSelector value="en" onChange={mockOnChange} />);

    expect(screen.getByRole('radio', { name: /english language/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /french language/i })).toBeInTheDocument();
  });

  it('should show check mark on selected option', () => {
    const mockOnChange = vi.fn();

    renderWithProviders(<LanguageSelector value="fr" onChange={mockOnChange} />);

    const frenchOption = screen.getByRole('radio', { name: /french language/i });
    expect(frenchOption).toHaveTextContent('✓');
  });

  it('should support keyboard navigation', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    renderWithProviders(<LanguageSelector value="en" onChange={mockOnChange} />);

    const frenchOption = screen.getByRole('radio', { name: /french language/i });
    frenchOption.focus();
    await user.keyboard('{Enter}');

    expect(mockOnChange).toHaveBeenCalledWith('fr');
  });
});
