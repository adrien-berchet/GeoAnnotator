# Auto-Share Rules Tests

This directory contains comprehensive tests for the auto-share rules functionality.

## Test Files

### `AutoShareRulesList.test.tsx`
Tests the `AutoShareRulesList` component functionality:
- ✅ Empty state rendering
- ✅ Rules list display (active/inactive)
- ✅ Toggle active status
- ✅ Permission level changes
- ✅ Rule deletion with confirmation
- ✅ Error handling and display
- ✅ Loading states and disabled controls
- ✅ "Share All" badge display
- ✅ Permission color classes

**15 tests** covering all user interactions and edge cases.

### `AutoShareRulesList.darkmode.test.tsx`
Tests dark mode compatibility:
- ✅ CSS variable usage for backgrounds
- ✅ Inactive class application
- ✅ Empty state styling
- ✅ Rule description styling
- ✅ Permission badge classes
- ✅ Overall structure for theme compatibility

**6 tests** ensuring proper dark mode support.

### `../pages/FriendDetailPage.optimistic-update.test.tsx`
Tests optimistic UI updates in the FriendDetailPage:
- ✅ Optimistic status toggle without flickering
- ✅ Optimistic permission changes
- ✅ Revert on API failure
- ✅ Error messages on failure
- ✅ No reload on successful update
- ✅ Reload only on API failure
- ✅ Multiple rapid updates handling
- ✅ Inactive class updates optimistically

**8 tests** validating the optimistic update pattern.

## Total Coverage

**29 tests** ensuring:
1. All user interactions work correctly
2. Errors are handled gracefully with clear feedback
3. Optimistic updates provide smooth UX without flickering
4. Dark mode styling is properly implemented
5. API failures properly revert UI state

## Running the Tests

Run all auto-share rules tests:
```bash
npm test -- tests/components/sharing/ tests/pages/FriendDetailPage.optimistic-update.test.tsx --run
```

Run specific test suite:
```bash
npm test -- AutoShareRulesList.test.tsx --run
npm test -- AutoShareRulesList.darkmode.test.tsx --run
npm test -- FriendDetailPage.optimistic-update.test.tsx --run
```

## Key Features Tested

### Optimistic Updates
The tests validate that:
1. UI updates immediately when user interacts (no waiting for API)
2. Changes are persisted to server in background
3. On API failure, UI reverts to previous state
4. Error messages are displayed clearly
5. No flickering or jarring state changes

### Dark Mode
The tests ensure:
1. CSS variables are used instead of hardcoded colors
2. `--color-bg-secondary` for card backgrounds
3. `--color-bg-tertiary` for inactive cards and descriptions
4. `--color-border-primary` for borders
5. Proper class application for theming

### Error Handling
The tests verify:
1. Clear error messages with context
2. Failed operations don't leave UI in broken state
3. Users can retry after errors
4. Loading states prevent duplicate actions
