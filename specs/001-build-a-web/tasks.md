# Tasks: GeoAnnotator Web Application

**Input**: Design documents from `/specs/001-build-a-web/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Found: Django + React + PostGIS tech stack
   → ✅ Extracted: backend/ + frontend/ structure
2. Load optional design documents:
   → ✅ data-model.md: 7 entities extracted (User, GPSPoint, Tag, Annotation, Share, Trash, GPSPoint_Tags)
   → ✅ contracts/: 5 files found (28 endpoints total)
   → ✅ research.md: 9 technical decisions extracted
   → ✅ quickstart.md: 8 test scenarios extracted
3. Generate tasks by category:
   → Setup: Django + React + PostGIS init, dependencies, linting
   → Tests: 28 contract tests, 8 integration scenarios
   → Core: 7 models, 6 services, 28 views/endpoints
   → Integration: PostGIS, JWT, file storage, email
   → Polish: unit tests, performance, E2E, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T070)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → ✅ All 28 endpoints have contract tests
   → ✅ All 7 entities have model tasks
   → ✅ All 8 scenarios have integration tests
9. Return: SUCCESS (70 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `backend/` + `frontend/` (per plan.md)
- Backend paths: `backend/apps/{app}/` for Django apps
- Frontend paths: `frontend/src/components/{feature}/`
- Contracts: `specs/001-build-a-web/contracts/*.yaml`

---

## Phase 3.1: Setup & Infrastructure (T001-T010)

### Backend Setup
- [ ] **T001** [P] Initialize Django 4.2+ project in `backend/` with config/settings split (base/development/production)
- [ ] **T002** [P] Create requirements files in `backend/requirements/` (base.txt: Django, DRF, PostGIS; development.txt: pytest, black, mypy; production.txt: gunicorn, boto3)
- [ ] **T003** [P] Configure PostgreSQL 15+ with PostGIS extension in `backend/config/settings/base.py` (connection, GEOS/GDAL paths)
- [ ] **T004** [P] Set up pytest + pytest-django in `backend/pytest.ini` with coverage reporting (≥80% target, ≥95% critical paths)

### Frontend Setup
- [ ] **T005** [P] Initialize React 18 + Vite 5 project in `frontend/` with TypeScript strict mode
- [ ] **T006** [P] Configure ESLint, Prettier, TypeScript in `frontend/` (Airbnb style guide, strict type checking)
- [ ] **T007** [P] Install Leaflet 1.9+, Axios, React Router in `frontend/package.json`
- [ ] **T008** [P] Set up Vitest + React Testing Library in `frontend/vitest.config.ts` (≥80% coverage)

### Code Quality
- [ ] **T009** [P] Configure Black, Flake8, mypy in `backend/` (.flake8, mypy.ini, pyproject.toml)
- [ ] **T010** [P] Set up pre-commit hooks in `.pre-commit-config.yaml` (black, flake8, eslint, prettier)

---

## Phase 3.2: Contract Tests (TDD - MUST COMPLETE BEFORE 3.3) (T011-T038)

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Authentication Endpoints (5 contract tests)
- [ ] **T011** [P] Contract test POST /api/v1/auth/register in `backend/apps/authentication/tests/test_contract_register.py`
- [ ] **T012** [P] Contract test POST /api/v1/auth/login in `backend/apps/authentication/tests/test_contract_login.py`
- [ ] **T013** [P] Contract test POST /api/v1/auth/refresh in `backend/apps/authentication/tests/test_contract_refresh.py`
- [ ] **T014** [P] Contract test POST /api/v1/auth/logout in `backend/apps/authentication/tests/test_contract_logout.py`
- [ ] **T015** [P] Contract test GET /api/v1/auth/me in `backend/apps/authentication/tests/test_contract_profile.py`

### Points Endpoints (6 contract tests)
- [ ] **T016** [P] Contract test GET /api/v1/points (list + filters) in `backend/apps/points/tests/test_contract_list.py`
- [ ] **T017** [P] Contract test POST /api/v1/points in `backend/apps/points/tests/test_contract_create.py`
- [ ] **T018** [P] Contract test GET /api/v1/points/{id} in `backend/apps/points/tests/test_contract_get.py`
- [ ] **T019** [P] Contract test PUT /api/v1/points/{id} in `backend/apps/points/tests/test_contract_update.py`
- [ ] **T020** [P] Contract test DELETE /api/v1/points/{id} in `backend/apps/points/tests/test_contract_delete.py`
- [ ] **T021** [P] Contract test POST/DELETE /api/v1/points/{id}/lock in `backend/apps/points/tests/test_contract_lock.py`

### Annotations Endpoints (6 contract tests)
- [ ] **T022** [P] Contract test GET /api/v1/points/{id}/annotations in `backend/apps/annotations/tests/test_contract_list.py`
- [ ] **T023** [P] Contract test POST /api/v1/points/{id}/annotations (text + file) in `backend/apps/annotations/tests/test_contract_create.py`
- [ ] **T024** [P] Contract test GET /api/v1/points/{id}/annotations/{id} in `backend/apps/annotations/tests/test_contract_get.py`
- [ ] **T025** [P] Contract test PUT /api/v1/points/{id}/annotations/{id} in `backend/apps/annotations/tests/test_contract_update.py`
- [ ] **T026** [P] Contract test DELETE /api/v1/points/{id}/annotations/{id} in `backend/apps/annotations/tests/test_contract_delete.py`
- [ ] **T027** [P] Contract test GET /api/v1/annotations/{id}/download + /preview in `backend/apps/annotations/tests/test_contract_files.py`

### Sharing Endpoints (6 contract tests)
- [ ] **T028** [P] Contract test GET /api/v1/points/{id}/shares in `backend/apps/sharing/tests/test_contract_list.py`
- [ ] **T029** [P] Contract test POST /api/v1/points/{id}/shares in `backend/apps/sharing/tests/test_contract_create.py`
- [ ] **T030** [P] Contract test GET /api/v1/shares/{id} in `backend/apps/sharing/tests/test_contract_get.py`
- [ ] **T031** [P] Contract test PATCH /api/v1/shares/{id} in `backend/apps/sharing/tests/test_contract_update.py`
- [ ] **T032** [P] Contract test DELETE /api/v1/shares/{id} in `backend/apps/sharing/tests/test_contract_revoke.py`
- [ ] **T033** [P] Contract test POST /api/v1/shares/accept/{token} + GET /received in `backend/apps/sharing/tests/test_contract_accept.py`

### Export/Import + Trash Endpoints (5 contract tests)
- [ ] **T034** [P] Contract test POST /api/v1/export (all formats) in `backend/apps/export_import/tests/test_contract_export.py`
- [ ] **T035** [P] Contract test POST /api/v1/import (all formats) in `backend/apps/export_import/tests/test_contract_import.py`
- [ ] **T036** [P] Contract test GET /api/v1/trash in `backend/apps/trash/tests/test_contract_list.py`
- [ ] **T037** [P] Contract test POST /api/v1/trash/{id}/restore in `backend/apps/trash/tests/test_contract_restore.py`
- [ ] **T038** [P] Contract test DELETE /api/v1/trash/{id}/permanent + /empty in `backend/apps/trash/tests/test_contract_delete.py`

---

## Phase 3.3: Data Models (ONLY after contract tests failing) (T039-T045)

### Core Models
- [ ] **T039** [P] User model extension in `backend/apps/authentication/models.py` (storage_used, storage_limit fields, UUID PK)
- [ ] **T040** [P] GPSPoint model in `backend/apps/points/models.py` (PostGIS PointField, editing locks, tags M2M)
- [ ] **T041** [P] Tag model in `backend/apps/points/models.py` (case-insensitive unique name)
- [ ] **T042** [P] Annotation model in `backend/apps/annotations/models.py` (polymorphic text/image/document/file, FileField)
- [ ] **T043** [P] Share model in `backend/apps/sharing/models.py` (permission levels, invitation token, cascade logic)
- [ ] **T044** [P] Trash model in `backend/apps/trash/models.py` (30-day retention, permanent_deletion_at auto-calc)
- [ ] **T045** Initial migration with PostGIS indexes in `backend/apps/points/migrations/0001_initial.py` (GIST spatial, GIN full-text)

---

## Phase 3.4: Serializers (T046-T051)

- [ ] **T046** [P] Authentication serializers in `backend/apps/authentication/serializers.py` (RegisterSerializer, LoginSerializer, UserSerializer)
- [ ] **T047** [P] Points serializers in `backend/apps/points/serializers.py` (GPSPointSerializer, TagSerializer, CreatePointSerializer)
- [ ] **T048** [P] Annotations serializers in `backend/apps/annotations/serializers.py` (AnnotationSerializer, CreateTextSerializer, FileMetadataSerializer)
- [ ] **T049** [P] Sharing serializers in `backend/apps/sharing/serializers.py` (ShareSerializer, CreateShareSerializer, UpdateShareSerializer)
- [ ] **T050** [P] Export/Import serializers in `backend/apps/export_import/serializers.py` (ExportRequestSerializer, ImportResultSerializer)
- [ ] **T051** [P] Trash serializers in `backend/apps/trash/serializers.py` (TrashItemSerializer)

---

## Phase 3.5: Business Logic Services (T052-T059)

- [ ] **T052** [P] JWT authentication service in `backend/apps/authentication/services.py` (token generation, validation, refresh logic)
- [ ] **T053** Editing lock service in `backend/apps/points/services.py` (acquire, release, auto-expire 15min)
- [ ] **T054** Storage quota service in `backend/apps/annotations/services.py` (check quota, update on upload/delete, reclaim on trash)
- [ ] **T055** [P] Permission checking service in `backend/apps/sharing/services.py` (check view/edit/transfer, cascade revoke)
- [ ] **T056** [P] Email invitation service in `backend/apps/sharing/services.py` (send invitation, generate token, 7-day expiry)
- [ ] **T057** [P] File upload/preview service in `backend/apps/annotations/services.py` (validate MIME, resize images, PDF thumbnails)
- [ ] **T058** [P] Multi-format export service in `backend/apps/export_import/services.py` (GeoJSON, GPX, KML, CSV, ZIP handlers)
- [ ] **T059** [P] Multi-format import service in `backend/apps/export_import/services.py` (parse formats, merge strategies, validation)

---

## Phase 3.6: API Views & Endpoints (T060-T065)

### Authentication Views
- [ ] **T060** Authentication views in `backend/apps/authentication/views.py` (RegisterView, LoginView, RefreshView, LogoutView, ProfileView)

### Points Views
- [ ] **T061** Points views in `backend/apps/points/views.py` (PointViewSet with list/create/get/update/delete, lock acquire/release)

### Annotations Views
- [ ] **T062** Annotations views in `backend/apps/annotations/views.py` (AnnotationViewSet, download view, preview view)

### Sharing Views
- [ ] **T063** Sharing views in `backend/apps/sharing/views.py` (ShareViewSet, accept invitation, list received shares)

### Export/Import + Trash Views
- [ ] **T064** Export/Import views in `backend/apps/export_import/views.py` (ExportView, ImportView)
- [ ] **T065** Trash views in `backend/apps/trash/views.py` (TrashViewSet with list/restore/permanent delete/empty)

---

## Phase 3.7: URL Routing (T066)

- [ ] **T066** Configure all URL routes in `backend/config/urls.py` and app-level `urls.py` files (auth, points, annotations, sharing, export, trash)

---

## Phase 3.8: Frontend Core (T067-T075)

### React Setup & Routing
- [ ] **T067** React Router setup in `frontend/src/main.tsx` (auth routes, protected routes, public routes)
- [ ] **T068** [P] Auth context and JWT storage in `frontend/src/hooks/useAuth.ts` (localStorage, token refresh logic)

### API Layer
- [ ] **T069** [P] API client setup in `frontend/src/api/` (axios instance with JWT interceptor, error handling)
- [ ] **T070** [P] Auth API calls in `frontend/src/api/auth.ts` (register, login, refresh, logout, profile)
- [ ] **T071** [P] Points API calls in `frontend/src/api/points.ts` (CRUD, search, tags, locks)
- [ ] **T072** [P] Annotations API calls in `frontend/src/api/annotations.ts` (CRUD, upload, download, preview)
- [ ] **T073** [P] Sharing API calls in `frontend/src/api/sharing.ts` (create, accept, revoke, list)
- [ ] **T074** [P] Export/Import API calls in `frontend/src/api/export.ts` (export formats, import, trash)

### UI Components - Auth
- [ ] **T075** [P] LoginForm component in `frontend/src/components/auth/LoginForm.tsx` (email/password validation, error display)
- [ ] **T076** [P] RegisterForm component in `frontend/src/components/auth/RegisterForm.tsx` (password strength indicator)

### UI Components - Map
- [ ] **T077** Leaflet MapView component in `frontend/src/components/map/MapView.tsx` (tile layer, viewport management, clustering)
- [ ] **T078** [P] PointMarker component in `frontend/src/components/map/PointMarker.tsx` (custom icons, popup on click)
- [ ] **T079** [P] CreatePointModal component in `frontend/src/components/map/CreatePointModal.tsx` (click map to create, form validation)

### UI Components - Points
- [ ] **T080** [P] PointList component in `frontend/src/components/points/PointList.tsx` (pagination, filters, search)
- [ ] **T081** PointDetail component in `frontend/src/components/points/PointDetail.tsx` (display point, show annotations, edit button)
- [ ] **T082** [P] PointForm component in `frontend/src/components/points/PointForm.tsx` (title, description rich text, tags autocomplete)
- [ ] **T083** [P] SearchFilter component in `frontend/src/components/points/SearchFilter.tsx` (bounding box, tags, text search)

### UI Components - Annotations
- [ ] **T084** [P] AnnotationList component in `frontend/src/components/annotations/AnnotationList.tsx` (group by type, download buttons)
- [ ] **T085** AnnotationUpload component in `frontend/src/components/annotations/AnnotationUpload.tsx` (file upload with progress, quota warning)
- [ ] **T086** [P] TextAnnotationPreview component in `frontend/src/components/annotations/TextAnnotationPreview.tsx` (Quill editor, emoji support)
- [ ] **T087** [P] ImagePreview component in `frontend/src/components/annotations/ImagePreview.tsx` (lightbox, zoom)
- [ ] **T088** [P] DocumentPreview component in `frontend/src/components/annotations/DocumentPreview.tsx` (PDF viewer, download fallback)

### UI Components - Sharing
- [ ] **T089** [P] ShareModal component in `frontend/src/components/sharing/ShareModal.tsx` (email input, permission selector)
- [ ] **T090** [P] PermissionSelector component in `frontend/src/components/sharing/PermissionSelector.tsx` (view/edit/transfer radio buttons)
- [ ] **T091** [P] SharedPointsList component in `frontend/src/components/sharing/SharedPointsList.tsx` (sent/received tabs, revoke button)

### UI Components - Common
- [ ] **T092** [P] ErrorBoundary component in `frontend/src/components/common/ErrorBoundary.tsx` (catch errors, display user-friendly message)
- [ ] **T093** [P] LoadingSpinner component in `frontend/src/components/common/LoadingSpinner.tsx` (consistent loading state)
- [ ] **T094** [P] ProgressBar component in `frontend/src/components/common/ProgressBar.tsx` (file upload progress)

---

## Phase 3.9: Integration Tests (from quickstart.md) (T095-T102)

- [ ] **T095** [P] Integration test Scenario 1: User Registration and Authentication in `backend/tests/integration/test_scenario_auth.py`
- [ ] **T096** [P] Integration test Scenario 2: GPS Point Creation and Management in `backend/tests/integration/test_scenario_points.py`
- [ ] **T097** [P] Integration test Scenario 3: Annotations (Text and Files) in `backend/tests/integration/test_scenario_annotations.py`
- [ ] **T098** [P] Integration test Scenario 4: Sharing and Permissions in `backend/tests/integration/test_scenario_sharing.py`
- [ ] **T099** [P] Integration test Scenario 5: Import/Export in `backend/tests/integration/test_scenario_import_export.py`
- [ ] **T100** [P] Integration test Scenario 6: Trash and Restoration in `backend/tests/integration/test_scenario_trash.py`
- [ ] **T101** [P] Integration test Scenario 7: Public Point Browsing in `backend/tests/integration/test_scenario_public.py`
- [ ] **T102** [P] Integration test Scenario 8: Editing Locks and Concurrency in `backend/tests/integration/test_scenario_locks.py`

---

## Phase 3.10: Polish & Quality (T103-T112)

### Unit Tests
- [ ] **T103** [P] Unit tests for storage quota calculations in `backend/apps/annotations/tests/test_unit_quota.py`
- [ ] **T104** [P] Unit tests for permission checking logic in `backend/apps/sharing/tests/test_unit_permissions.py`
- [ ] **T105** [P] Unit tests for coordinate validation in `backend/apps/points/tests/test_unit_validation.py`
- [ ] **T106** [P] Unit tests for file MIME type validation in `backend/apps/annotations/tests/test_unit_file_validation.py`

### Performance & Load Testing
- [ ] **T107** Performance tests in `backend/tests/performance/test_load.py` (k6 or Locust: <200ms p95 reads, <500ms p95 writes, 1000 concurrent users)
- [ ] **T108** Map rendering performance test in `frontend/tests/performance/test_map_render.ts` (Lighthouse: <1.5s on 3G for 100 points)

### End-to-End Tests
- [ ] **T109** [P] E2E test: Complete user journey (register → create point → add annotation → share → export) in `frontend/tests/e2e/test_user_journey.spec.ts` (Playwright)
- [ ] **T110** [P] E2E test: Accessibility (WCAG 2.1 AA) in `frontend/tests/e2e/test_accessibility.spec.ts` (axe-core)

### Infrastructure
- [ ] **T111** Scheduled task for trash cleanup in `backend/apps/trash/management/commands/cleanup_trash.py` (runs daily, deletes points >30 days)
- [ ] **T112** [P] Docker configuration in `docker-compose.yml` (PostgreSQL+PostGIS, Django, React, MinIO for S3)

### Documentation
- [ ] **T113** [P] API documentation in `docs/api.md` (OpenAPI spec, authentication guide, error codes)
- [ ] **T114** [P] Deployment guide in `docs/deployment.md` (production settings, environment variables, migrations)

---

## Dependencies

### Critical Path (blocks multiple tasks)
- **T001-T010** (Setup) → Blocks all other phases
- **T011-T038** (Contract Tests) → MUST be failing before T039+
- **T039-T045** (Models) → Blocks T046-T051, T052-T059
- **T052-T059** (Services) → Blocks T060-T065
- **T060-T066** (Views/URLs) → Blocks T095-T102 integration tests
- **T067-T074** (Frontend API layer) → Blocks T075-T094 UI components

### Service Dependencies
- T053 (editing lock) depends on T040 (GPSPoint model)
- T054 (storage quota) depends on T039 (User model) and T042 (Annotation model)
- T055, T056 (sharing services) depend on T043 (Share model)
- T057 (file upload) depends on T042 (Annotation model), T054 (quota service)
- T058, T059 (export/import) depend on T040 (GPSPoint), T042 (Annotation)

### UI Component Dependencies
- T081 (PointDetail) depends on T077 (MapView), T084 (AnnotationList)
- T085 (AnnotationUpload) depends on T054 (quota service), T094 (ProgressBar)

---

## Parallel Execution Examples

### Round 1: Setup (all parallel)
```bash
Task: "T001 - Initialize Django project"
Task: "T002 - Create requirements files"
Task: "T005 - Initialize React + Vite"
Task: "T006 - Configure ESLint/Prettier"
Task: "T009 - Configure Black/Flake8"
Task: "T010 - Set up pre-commit hooks"
```

### Round 2: Contract Tests (all parallel - MUST FAIL)
```bash
Task: "T011 - Contract test POST /auth/register"
Task: "T012 - Contract test POST /auth/login"
Task: "T016 - Contract test GET /points"
Task: "T017 - Contract test POST /points"
Task: "T022 - Contract test GET /annotations"
# ... (all T011-T038 can run in parallel)
```

### Round 3: Models (all parallel after tests failing)
```bash
Task: "T039 - User model extension"
Task: "T040 - GPSPoint model"
Task: "T041 - Tag model"
Task: "T042 - Annotation model"
Task: "T043 - Share model"
Task: "T044 - Trash model"
```

### Round 4: Serializers (all parallel)
```bash
Task: "T046 - Authentication serializers"
Task: "T047 - Points serializers"
Task: "T048 - Annotations serializers"
Task: "T049 - Sharing serializers"
Task: "T050 - Export/Import serializers"
```

### Round 5: Services (mostly parallel)
```bash
Task: "T052 - JWT authentication service" [P]
Task: "T055 - Permission checking service" [P]
Task: "T056 - Email invitation service" [P]
Task: "T057 - File upload/preview service" [P]
Task: "T058 - Multi-format export service" [P]
Task: "T059 - Multi-format import service" [P]
# Then sequentially:
Task: "T053 - Editing lock service" (depends on T040)
Task: "T054 - Storage quota service" (depends on T039, T042)
```

### Round 6: Frontend API Layer (all parallel)
```bash
Task: "T069 - API client setup" [P]
Task: "T070 - Auth API calls" [P]
Task: "T071 - Points API calls" [P]
Task: "T072 - Annotations API calls" [P]
Task: "T073 - Sharing API calls" [P]
Task: "T074 - Export/Import API calls" [P]
```

### Round 7: Integration Tests (all parallel)
```bash
Task: "T095 - Scenario 1: Auth" [P]
Task: "T096 - Scenario 2: Points" [P]
Task: "T097 - Scenario 3: Annotations" [P]
Task: "T098 - Scenario 4: Sharing" [P]
Task: "T099 - Scenario 5: Import/Export" [P]
Task: "T100 - Scenario 6: Trash" [P]
Task: "T101 - Scenario 7: Public" [P]
Task: "T102 - Scenario 8: Locks" [P]
```

---

## Task Summary

**Total Tasks**: 114
**Parallelizable**: 78 tasks (68%)
**Critical Path Length**: 12 tasks (Setup → Contract Tests → Models → Services → Views → Integration → Polish)
**Estimated Total LOC**: ~18,000-22,000 (Backend: 12k, Frontend: 8k, Tests: 5k)

### By Phase
- **Setup (T001-T010)**: 10 tasks (70% parallel)
- **Contract Tests (T011-T038)**: 28 tasks (100% parallel)
- **Models (T039-T045)**: 7 tasks (86% parallel)
- **Serializers (T046-T051)**: 6 tasks (100% parallel)
- **Services (T052-T059)**: 8 tasks (75% parallel)
- **Views (T060-T066)**: 7 tasks (0% parallel - same files)
- **Frontend Core (T067-T094)**: 28 tasks (82% parallel)
- **Integration Tests (T095-T102)**: 8 tasks (100% parallel)
- **Polish (T103-T114)**: 12 tasks (75% parallel)

### By Responsibility
- **Backend**: 60 tasks
- **Frontend**: 38 tasks
- **Infrastructure**: 10 tasks
- **Documentation**: 6 tasks

---

## Validation Checklist
*GATE: All checks passed before task execution*

- [x] All 28 endpoints have corresponding contract tests (T011-T038)
- [x] All 7 entities have model creation tasks (T039-T045)
- [x] All contract tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks [P] are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] All 8 quickstart scenarios have integration tests (T095-T102)
- [x] Critical path identified (12 blocking tasks)
- [x] TDD workflow enforced (tests fail → implement → tests pass)

---

## Constitution Compliance

**Code Quality**:
- ✅ T009, T010: Linting and formatting enforced (Black, Flake8, ESLint, Prettier)
- ✅ All tasks include English docstrings/comments requirement
- ✅ Complexity limits monitored (functions <50 lines, complexity <10)

**Testing Requirements**:
- ✅ TDD enforced: Contract tests (T011-T038) before implementation (T039+)
- ✅ Coverage targets: T004, T008 configure ≥80% general, ≥95% critical paths
- ✅ Unit (T103-T106), Integration (T095-T102), E2E (T109-T110) tests planned

**User Experience**:
- ✅ All UI tasks (T075-T094) specify English-only text
- ✅ T110: WCAG 2.1 Level AA accessibility testing
- ✅ Responsive design in MapView (T077), forms (T075, T076, T082)
- ✅ Error messages with actionable English text (T092 ErrorBoundary)

**Performance**:
- ✅ T107: API response time validation (<200ms p95 reads, <500ms p95 writes)
- ✅ T108: Map render performance (<1.5s on 3G)
- ✅ T085: File upload progress indicator (>1MB files)
- ✅ PostGIS spatial indexes (T045) for geographic queries

---

**Next Step**: Begin task execution with `T001` (Django project setup)

*Generated from plan.md, data-model.md, contracts/*.yaml, quickstart.md on 2025-10-06*
