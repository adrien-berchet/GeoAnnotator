# CSS Architecture Documentation

## Overview

The frontend styling has been harmonized and restructured to use a centralized design system with CSS variables. This makes maintenance easier and ensures consistency across all pages.

## Structure

### Core Files

1. **`variables.css`** - Design System Foundation
   - All CSS custom properties (colors, spacing, typography, shadows, etc.)
   - Light and dark mode theme definitions
   - Single source of truth for all design tokens

2. **`theme.css`** - Base HTML Styles
   - Global resets and base HTML element styles
   - Typography defaults
   - Form element base styles

3. **`components.css`** - Reusable Component Classes
   - Buttons (`.btn`, `.btn-primary`, `.btn-danger`, etc.)
   - Cards (`.card`, `.card-header`, `.card-footer`)
   - Forms (`.form-group`, `.form-input`, `.form-label`)
   - Badges, tags, alerts
   - Empty states and error containers
   - Loading spinners
   - Layout utilities (`.container`, `.grid`, flex utilities)

4. **`markdown-editor.css`** - Markdown Editor Styles
   - Custom styling for `@uiw/react-md-editor`
   - Dark mode support

### Import Order

```css
/* index.css */
@import './styles/variables.css';  /* 1. Design tokens first */
@import './styles/theme.css';      /* 2. Base styles */
@import './styles/components.css'; /* 3. Reusable components */
```

## CSS Variables

All design tokens are defined as CSS variables in `variables.css`:

### Colors
- **Primary:** `--color-primary`, `--color-primary-hover`, `--color-primary-light`, `--color-primary-dark`
- **Semantic:** `--color-success`, `--color-danger`, `--color-warning`, `--color-info`
- **Backgrounds:** `--color-bg-primary`, `--color-bg-secondary`, `--color-bg-tertiary`
- **Text:** `--color-text-primary`, `--color-text-secondary`, `--color-text-tertiary`
- **Borders:** `--color-border-primary`, `--color-border-secondary`

### Spacing
```css
--spacing-xs: 0.25rem;  /* 4px */
--spacing-sm: 0.5rem;   /* 8px */
--spacing-md: 0.75rem;  /* 12px */
--spacing-lg: 1rem;     /* 16px */
--spacing-xl: 1.5rem;   /* 24px */
--spacing-2xl: 2rem;    /* 32px */
--spacing-3xl: 3rem;    /* 48px */
--spacing-4xl: 4rem;    /* 64px */
```

### Typography
- **Sizes:** `--font-size-xs` through `--font-size-3xl`
- **Weights:** `--font-weight-normal`, `--font-weight-medium`, `--font-weight-semibold`, `--font-weight-bold`
- **Line Heights:** `--line-height-tight`, `--line-height-normal`, `--line-height-relaxed`

### Border Radius
```css
--radius-xs: 2px;
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-xl: 12px;
--radius-full: 9999px;
```

### Shadows
- `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`
- `--shadow-focus-ring` for focus states

### Transitions
- `--transition-fast: 0.15s`
- `--transition-base: 0.2s`
- `--transition-slow: 0.3s`

## Dark Mode

Dark mode is automatically handled through CSS variables with the `[data-theme='dark']` selector in `variables.css`. When the theme changes, all colors, shadows, and other design tokens automatically update.

**No need to define dark mode styles in individual component or page CSS files.**

## Page-Specific CSS

Page CSS files (e.g., `MapPage.css`, `SettingsPage.css`) should only contain:
- Page-specific layout and positioning
- Unique component variations needed only for that page
- **NOT**: reusable patterns like buttons, cards, forms, error states

### Example
```css
/* Good - Page-specific layout */
.map-page {
  position: relative;
  height: calc(100vh - var(--navbar-height));
}

/* Bad - Should use .btn-primary from components.css */
.my-button {
  background: var(--color-primary);
  padding: var(--spacing-md);
  /* ... */
}
```

## Common Patterns

### Buttons
Use existing button classes instead of creating new ones:
```html
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
<button class="btn btn-danger">Delete</button>
<button class="btn btn-sm">Small Button</button>
```

### Cards
```html
<div class="card">
  <div class="card-header">
    <h2 class="card-title">Title</h2>
  </div>
  <div class="card-body">Content</div>
  <div class="card-footer">Footer</div>
</div>
```

### Forms
```html
<div class="form-group">
  <label class="form-label">Label</label>
  <input class="form-input" type="text" />
  <span class="form-hint">Helper text</span>
</div>
```

### Error States
```html
<div class="error-container">
  <h2>Error Title</h2>
  <p>Error description</p>
</div>
```

### Loading Spinner
```html
<div class="loading">
  <div class="spinner"></div>
</div>
```

## Best Practices

1. **Always use CSS variables** - Never hardcode colors, spacing, or other design tokens
2. **Reuse common classes** - Check `components.css` before creating new styles
3. **No dark mode in pages** - All theme handling is centralized in `variables.css`
4. **Mobile-first** - Use min-width media queries when possible
5. **Semantic naming** - Use descriptive class names that reflect purpose, not appearance

## Changes Made

### Removed
- `themes.css` - Merged into `variables.css`
- Duplicate error containers, loading spinners, and empty states from page files
- Dark mode overrides from individual page CSS files
- Hardcoded color values and spacing

### Added
- Comprehensive CSS variable system in `variables.css`
- Common component patterns in `components.css`
- Loading spinner animations
- Error and success message styles
- Visually-hidden utility class

### Updated
- All page CSS files to use CSS variables instead of hardcoded values
- Button, card, and form styles consolidated
- Consistent spacing and typography across all pages
- Unified dark mode through CSS variables

## File Count Reduction

**Before:** 41 CSS files
**After:** Consolidated common patterns, removed `themes.css`

The number of page-specific CSS files remains the same, but each file is now smaller and focuses only on page-specific layout rather than duplicating common patterns.
