/**
 * Tests for ThemeSelector component.
 *
 * Tests theme selection UI with auto/light/dark options.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ThemeSelector from '@/components/settings/ThemeSelector';

describe('ThemeSelector Component', () => {
  it('should render three theme options', () => {
    const mockOnChange = vi.fn();

    render(<ThemeSelector value="auto" onChange={mockOnChange} />);

    expect(screen.getByText(/auto/i)).toBeInTheDocument();
    expect(screen.getByText(/light/i)).toBeInTheDocument();
    expect(screen.getByText(/dark/i)).toBeInTheDocument();
  });

  it('should call onChange when option is selected', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    render(<ThemeSelector value="auto" onChange={mockOnChange} />);

    const lightOption = screen.getByRole('radio', { name: /light theme/i });
    await user.click(lightOption);

    expect(mockOnChange).toHaveBeenCalledWith('light');
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  it('should highlight selected value', () => {
    const mockOnChange = vi.fn();

    const { rerender } = render(
      <ThemeSelector value="auto" onChange={mockOnChange} />
    );

    const autoOption = screen.getByRole('radio', { name: /auto theme/i });
    expect(autoOption).toHaveClass('selected');

    // Rerender with different value
    rerender(<ThemeSelector value="dark" onChange={mockOnChange} />);

    const darkOption = screen.getByRole('radio', { name: /dark theme/i });
    expect(darkOption).toHaveClass('selected');
    expect(autoOption).not.toHaveClass('selected');
  });

  it('should support keyboard navigation with arrow keys', async () => {
    const mockOnChange = vi.fn();
    const user = userEvent.setup();

    render(<ThemeSelector value="auto" onChange={mockOnChange} />);

    const autoOption = screen.getByRole('radio', { name: /auto theme/i });
    autoOption.focus();

    // Arrow right should move to next option
    await user.keyboard('{ArrowRight}');
    expect(mockOnChange).toHaveBeenCalledWith('light');

    // Arrow left should move to previous option
    await user.keyboard('{ArrowLeft}');
    expect(mockOnChange).toHaveBeenCalledWith('dark');
  });

  it('should display icons for each theme option', () => {
    const mockOnChange = vi.fn();

    render(<ThemeSelector value="auto" onChange={mockOnChange} />);

    // Check for theme icons (using aria-hidden spans)
    const icons = document.querySelectorAll('.theme-icon');
    expect(icons.length).toBe(3);
  });

  it('should have accessible labels', () => {
    const mockOnChange = vi.fn();

    render(<ThemeSelector value="auto" onChange={mockOnChange} />);

    expect(screen.getByRole('radiogroup', { name: /theme selection/i })).toBeInTheDocument();
  });

  it('should update aria-checked attribute on selection', () => {
    const mockOnChange = vi.fn();

    render(<ThemeSelector value="dark" onChange={mockOnChange} />);

    const darkOption = screen.getByRole('radio', { name: /dark theme/i });
    expect(darkOption).toHaveAttribute('aria-checked', 'true');

    const lightOption = screen.getByRole('radio', { name: /light theme/i });
    expect(lightOption).toHaveAttribute('aria-checked', 'false');
  });
});
