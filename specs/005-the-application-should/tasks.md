# Tasks: Internationalization and Language Selection

**Feature Branch**: `005-the-application-should`
**Spec**: /home/adrien/Work/Perso/geoannotator/specs/005-the-application-should/spec.md
**Plan**: /home/adrien/Work/Perso/geoannotator/specs/005-the-application-should/plan.md

---

## Setup Tasks

- T001: Initialize i18n structure in frontend (`frontend/src/assets/` for translation files)
- T002: Add language context/provider in frontend (`frontend/src/contexts/LanguageContext.tsx`)
- T003: Add language selector component (`frontend/src/components/LanguageSelector.tsx`)
- T004: Add backend API endpoints for language preference (`backend/apps/settings/views.py`, `urls.py`)
- T005: Add model for user language preference (`backend/apps/settings/models.py`)
- T006: Add migration for user language preference model (`backend/apps/settings/migrations/`)
- T007: Add tests for backend language API (`backend/apps/settings/tests/`)

## Test Tasks [P]

- T008 [P]: Write unit tests for LanguageContext and selector (frontend)
- T009 [P]: Write integration tests for language switching (frontend)
- T010 [P]: Write contract tests for backend language API (backend)
- T011 [P]: Write tests for fallback logic (frontend/backend)

## Core Tasks

- T012: Implement translation loading and fallback logic (`frontend/src/utils/i18n.ts`)
- T013: Implement persistence of language preference in backend (authenticated) and local storage (anonymous) (`frontend/src/utils/i18n.ts`, `backend/apps/settings/services.py`)
- T014: Implement UI update on language change (`frontend/src/pages/SettingsPage.tsx`)
- T015: Implement backend logic for returning localized content (`backend/apps/annotations/views.py`)
- T016: Integrate language parameter in backend content endpoints (`backend/apps/annotations/urls.py`)

## Integration Tasks

- T017: Connect frontend to backend language API (`frontend/src/api/settings.ts`)
- T018: Ensure all pages/components use i18n context (`frontend/src/pages/`, `frontend/src/components/`)
- T019: Integrate translation files for English and French (`frontend/src/assets/en.json`, `frontend/src/assets/fr.json`)

## Polish Tasks [P]

- T020 [P]: Add accessibility checks for language selector and i18n
- T021 [P]: Add performance tests for language switching
- T022 [P]: Update documentation (`README.md`, feature docs)
- T023 [P]: Final code review and linting

---

## Parallel Execution Guidance

- Tasks marked [P] can be executed in parallel (e.g., T008, T009, T010, T011, T020, T021, T022, T023)
- Setup and core tasks should be completed sequentially due to dependencies
- Integration tasks can be started once core logic is in place

## Dependency Notes

- Backend model and API must be ready before frontend integration
- Translation files must be available before UI and tests
- Fallback logic should be tested after basic i18n is implemented

---

## Task Agent Commands (examples)

- `/run T008,T009,T010,T011` (parallel)
- `/run T001-T007` (sequential)
- `/run T012-T019` (sequential)
- `/run T020,T021,T022,T023` (parallel)

---

Total tasks: 23
