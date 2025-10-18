# Tasks: Show Device Position on Map

**Feature Branch**: `004-l-application-doit`
**Spec**: `/specs/004-l-application-doit/spec.md`
**Plan**: `/specs/004-l-application-doit/plan.md`

---

## Setup & Environment

- T001: Ensure all frontend dependencies are installed (React, Leaflet, TypeScript, Vitest)
- T002: Set up linting and type checking for frontend (ESLint, TypeScript config)

## Test-Driven Development (TDD)

- T003 [P]: Write integration test: blue dot appears at device position if available (frontend/src/pages/__tests__/)
- T004 [P]: Write integration test: blue dot moves in real time as position updates (frontend/src/pages/__tests__/)
- T005 [P]: Write integration test: user can recenter map on device position (frontend/src/pages/__tests__/)
- T006 [P]: Write integration test: clicking blue dot opens point creation panel with device position (frontend/src/pages/__tests__/)
- T007 [P]: Write integration test: user is notified if position is unavailable or permission denied (frontend/src/pages/__tests__/)

## Core Implementation

- T008: Implement DevicePosition model/hook (frontend/src/hooks/useDevicePosition.ts)
- T009: Implement BlueDot component (frontend/src/components/BlueDot.tsx)
- T010: Implement recenter map button and logic (frontend/src/components/RecenterButton.tsx)
- T011: Implement point creation panel logic for device position (frontend/src/pages/PointCreationPanel.tsx)
- T012: Implement notification system for permission denied/unavailable (frontend/src/components/Notification.tsx)

## Integration & Polish

- T013 [P]: Add accessibility features to BlueDot and notifications (ARIA, keyboard navigation)
- T014 [P]: Add responsive design and cross-browser testing (320px-2560px)
- T015 [P]: Add English documentation and code comments for all new files
- T016 [P]: Add unit tests for new hooks and components (frontend/src/components/__tests__/)
- T017 [P]: Performance test: blue dot update latency <500ms

---

## Parallel Execution Guidance

Tasks marked [P] can be executed in parallel:
- T003–T007: All integration tests can be written in parallel
- T013–T017: Accessibility, responsive design, documentation, unit tests, and performance tests can be done in parallel after core implementation

## Dependency Notes
- Setup (T001–T002) must be completed before any other task
- Integration tests (T003–T007) should be written before implementation (T008–T012)
- Core implementation (T008–T012) must be completed before polish/integration (T013–T017)

---

## Task Agent Commands (examples)
- `/run T003` (writes integration test for blue dot appearance)
- `/run T008` (implements device position hook)
- `/run T013` (adds accessibility features)

---

## Completion Criteria
- All tasks completed and passing tests
- Feature matches specification and plan
- Code quality, accessibility, and performance requirements met
