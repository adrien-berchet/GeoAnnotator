/**
 * Theme selector component for choosing application theme
 */

import React from 'react';
import type { ThemeMode } from '@/types/settings';
import './ThemeSelector.css';

interface ThemeSelectorProps {
  value: ThemeMode;
  onChange: (theme: ThemeMode) => void;
}

const themeOptions: Array<{ value: ThemeMode; label: string; icon: string }> = [
  { value: 'auto', label: 'Auto', icon: '🌓' },
  { value: 'light', label: 'Light', icon: '☀️' },
  { value: 'dark', label: 'Dark', icon: '🌙' },
];

function ThemeSelector({ value, onChange }: ThemeSelectorProps) {
  const handleKeyDown = (event: React.KeyboardEvent, currentTheme: ThemeMode) => {
    const currentIndex = themeOptions.findIndex((opt) => opt.value === currentTheme);

    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      const nextIndex = (currentIndex + 1) % themeOptions.length;
      onChange(themeOptions[nextIndex].value);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIndex = (currentIndex - 1 + themeOptions.length) % themeOptions.length;
      onChange(themeOptions[prevIndex].value);
    }
  };

  return (
    <div className="theme-selector" role="radiogroup" aria-label="Theme selection">
      {themeOptions.map((option) => {
        const isSelected = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-label={`${option.label} theme`}
            className={`theme-option ${isSelected ? 'selected' : ''}`}
            onClick={() => onChange(option.value)}
            onKeyDown={(e) => handleKeyDown(e, option.value)}
          >
            <span className="theme-icon" aria-hidden="true">
              {option.icon}
            </span>
            <span className="theme-label">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default ThemeSelector;
