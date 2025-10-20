# Tasks: Multilingual Point Type Names

**Input**: Design documents from `/specs/007-les-types-de/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
2. Load optional design documents: data-model.md, contracts/, research.md, quickstart.md
3. Generate tasks by category: Setup, Tests, Core, Integration, Polish
4. Apply task rules: [P] for parallel, TDD order, dependencies
5. Number tasks sequentially (T001, T002...)
6. Validate task completeness
```

## Phase 3.1: Setup
- [ ] T001 Create backend and frontend project structure per plan.md
- [ ] T002 Initialize backend Python project with Django, Django REST Framework, PostgreSQL dependencies in backend/
- [ ] T003 Initialize frontend TypeScript project with React, Vite in frontend/
- [ ] T004 [P] Configure linting and formatting tools for backend (e.g., flake8, black, isort)
- [ ] T005 [P] Configure linting and formatting tools for frontend (e.g., eslint, prettier)
- [ ] T006 [P] Configure type checking for backend (mypy)
- [ ] T007 [P] Configure type checking for frontend (tsc)
- [ ] T008 [P] Set up code coverage reporting for backend (pytest-cov)
- [ ] T009 [P] Set up code coverage reporting for frontend (vitest)

## Phase 3.2: Tests First (TDD)
- [ ] T010 [P] Contract test: List all point types in backend/tests/contract/test_point_types_list.py
- [ ] T011 [P] Contract test: Create a custom point type in backend/tests/contract/test_point_types_create.py
- [ ] T012 [P] Contract test: Get a point type by ID in backend/tests/contract/test_point_types_get.py
- [ ] T013 [P] Contract test: Update a custom point type (add translation) in backend/tests/contract/test_point_types_update.py
- [ ] T014 [P] Integration test: User views point types in preferred language in backend/tests/integration/test_point_types_language.py
- [ ] T015 [P] Integration test: Fallback logic for missing translation in backend/tests/integration/test_point_types_fallback.py
- [ ] T016 [P] Integration test: Prevent duplicate language entries in backend/tests/integration/test_point_types_duplicates.py
- [ ] T017 [P] Integration test: Prevent removal of last translation in backend/tests/integration/test_point_types_removal.py

## Phase 3.3: Core Implementation
- [ ] T018 [P] Implement PointType model in backend/src/models/point_type.py
- [ ] T019 [P] Implement User model (with language_preference) in backend/src/models/user.py
- [ ] T020 [P] Implement PointType service logic in backend/src/services/point_type_service.py
- [ ] T021 [P] Implement User service logic in backend/src/services/user_service.py
- [ ] T022 Implement API endpoint: GET /point-types/ in backend/src/api/point_types.py
- [ ] T023 Implement API endpoint: POST /point-types/ in backend/src/api/point_types.py
- [ ] T024 Implement API endpoint: GET /point-types/{id}/ in backend/src/api/point_types.py
- [ ] T025 Implement API endpoint: PATCH /point-types/{id}/ in backend/src/api/point_types.py
- [ ] T026 Implement fallback and translation logic in backend/src/services/point_type_service.py
- [ ] T027 Implement frontend UI: list point types in frontend/src/pages/PointTypesPage.tsx
- [ ] T028 Implement frontend UI: create/edit custom point type in frontend/src/pages/PointTypeEditPage.tsx
- [ ] T029 Implement frontend UI: translation management (add/remove) in frontend/src/components/PointTypeTranslations.tsx

## Phase 3.4: Integration
- [ ] T030 Connect backend to PostgreSQL (settings, migrations)
- [ ] T031 Connect frontend to backend API (service layer) in frontend/src/services/pointTypeService.ts
- [ ] T032 Implement error handling and user feedback in frontend/src/components/ErrorMessage.tsx
- [ ] T033 Implement accessibility checks (WCAG 2.1 AA) in frontend/src/components/PointTypeTranslations.tsx

## Phase 3.5: Polish
- [ ] T034 [P] Unit tests for backend validation logic in backend/tests/unit/test_point_type_validation.py
- [ ] T035 [P] Unit tests for frontend translation logic in frontend/tests/unit/test_point_type_translations.ts
- [ ] T036 [P] Performance tests for backend API (<200ms p95 reads, <500ms p95 writes) in backend/tests/performance/test_point_types_performance.py
- [ ] T037 [P] Update docs/api.md and user documentation for multilingual point types
- [ ] T038 [P] Refactor and remove duplication in backend/src/services/point_type_service.py
- [ ] T039 [P] Refactor and remove duplication in frontend/src/components/PointTypeTranslations.tsx
- [ ] T040 [P] Manual test: verify fallback and translation logic in UI

## Dependencies
- Setup (T001-T009) before all
- Tests (T010-T017) before implementation (T018-T032)
- Models (T018-T019) before services (T020-T021)
- Services before endpoints (T022-T026)
- Backend before frontend integration (T031)
- Implementation before polish (T034-T040)

## Parallel Example
```
# Launch contract and integration tests together:
Task: "Contract test: List all point types in backend/tests/contract/test_point_types_list.py"
Task: "Integration test: Fallback logic for missing translation in backend/tests/integration/test_point_types_fallback.py"
Task: "Unit tests for frontend translation logic in frontend/tests/unit/test_point_type_translations.ts"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
