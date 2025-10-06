# Implementation Plan: GeoAnnotator Web Application

**Branch**: `001-build-a-web` | **Date**: 2025-10-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-build-a-web/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ No NEEDS CLARIFICATION markers (all resolved in /clarify phase)
   → ✅ Project Type: web (frontend + backend)
   → ✅ Structure Decision: backend/ + frontend/ structure
3. Fill the Constitution Check section
   → ✅ Constitution loaded and checks defined
4. Evaluate Constitution Check section
   → ✅ No violations identified
   → ✅ Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✅ Research document created
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent file
   → ✅ All artifacts generated
7. Re-evaluate Constitution Check section
   → ✅ Post-Design Constitution Check PASS
8. Plan Phase 2 → Task generation approach described
9. STOP - Ready for /tasks command
```

## Summary

Build a comprehensive web application for geospatial annotation enabling field researchers to capture GPS points with rich multimedia annotations (text, images, documents), share with collaborators, and export/import data in standard formats. Core features include: user authentication with JWT, interactive Leaflet map with clustering, 1GB/file and 2GB/user storage limits, 30-day trash with immediate sharing disable, editing locks for concurrent access prevention, email-based sharing with view/edit/transfer permissions, and multi-format export (GeoJSON/GPX/KML/CSV + ZIP bundle).

**Technical Approach**: Django REST Framework backend with PostGIS-enabled PostgreSQL for native geospatial operations, React + Vite frontend with Leaflet for interactive mapping, JWT authentication via djangorestframework-simplejwt, file storage with quota tracking, and comprehensive test coverage (≥80% general, ≥95% auth/storage paths).

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: JavaScript/TypeScript (ES2022+)

**Primary Dependencies**:
- Backend: Django 4.2+, Django REST Framework 3.14+, djangorestframework-simplejwt, PostgreSQL 15+ with PostGIS extension
- Frontend: React 18+, Vite 5+, Leaflet 1.9+, Axios for API calls

**Storage**: PostgreSQL 15+ with PostGIS extension for native geographic coordinate handling, file storage for annotations (local or S3-compatible)

**Testing**:
- Backend: pytest, pytest-django, factory-boy for fixtures
- Frontend: Vitest, React Testing Library, Playwright for E2E

**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge latest 2 versions), responsive 320px-2560px

**Performance Goals**:
- API: <200ms p95 read, <500ms p95 write
- Map render: <1.5s p95 on 3G for 100 points
- Search: <500ms p95
- File upload: progress indicator >1MB
- Support 1000 concurrent users

**Constraints**:
- 1GB max file size per annotation
- 2GB total storage per user
- 255 char max title length
- 30-day trash retention
- JWT token expiration (1h access, 7d refresh)

**Scale/Scope**:
- Support ~10,000 registered users
- ~100,000 GPS points total
- ~500,000 annotations total
- Geographic operations optimized with PostGIS spatial indexes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Code Quality Standards**:
- [x] Code will adhere to linting and type checking standards (Black, Flake8, mypy for Python; ESLint, Prettier, TypeScript for frontend)
- [x] All code will be documented in English with clear API descriptions (docstrings, JSDoc)
- [x] Complexity limits will be respected (functions <50 lines, complexity <10)

**Testing Requirements**:
- [x] TDD approach planned (tests before implementation)
- [x] Coverage targets defined (≥80% general, ≥95% critical paths: auth, storage quota, permissions)
- [x] Unit, integration, and E2E test types identified

**User Experience Consistency**:
- [x] All UI/UX elements designed in English (US)
- [x] WCAG 2.1 Level AA accessibility considered (keyboard navigation, ARIA labels, contrast)
- [x] Responsive design planned (320px-2560px viewports with mobile-first approach)
- [x] Error messages planned with clear, actionable English text

**Performance Requirements**:
- [x] API response time targets defined (<200ms p95 reads, <500ms p95 writes)
- [x] Resource efficiency targets set (bundle size <300KB gzipped, memory <512MB)
- [x] Performance monitoring and load testing planned (Django Debug Toolbar, Lighthouse, k6)

## Project Structure

### Documentation (this feature)
```
specs/001-build-a-web/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── auth-endpoints.yaml
│   ├── points-endpoints.yaml
│   ├── annotations-endpoints.yaml
│   ├── sharing-endpoints.yaml
│   └── export-import-endpoints.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
backend/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── authentication/
│   │   ├── models.py        # User model extension
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── points/
│   │   ├── models.py        # GPSPoint, Tag
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py      # Business logic (editing locks, clustering)
│   │   ├── urls.py
│   │   └── tests/
│   ├── annotations/
│   │   ├── models.py        # Annotation
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py      # File upload, quota tracking, preview
│   │   ├── urls.py
│   │   └── tests/
│   ├── sharing/
│   │   ├── models.py        # Share, permissions
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py      # Email invitations, permission checks
│   │   ├── urls.py
│   │   └── tests/
│   ├── trash/
│   │   ├── models.py        # Trash, 30-day retention
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── cleanup_trash.py  # Scheduled task
│   │   ├── views.py
│   │   └── tests/
│   └── export_import/
│       ├── serializers.py
│       ├── views.py
│       ├── services.py      # GeoJSON/GPX/KML/CSV/ZIP handlers
│       ├── urls.py
│       └── tests/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── pytest.ini

frontend/
├── index.html
├── package.json
├── vite.config.js
├── tsconfig.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── auth.ts          # JWT auth API calls
│   │   ├── points.ts
│   │   ├── annotations.ts
│   │   ├── sharing.ts
│   │   └── export.ts
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── PasswordResetForm.tsx
│   │   ├── map/
│   │   │   ├── MapView.tsx
│   │   │   ├── PointMarker.tsx
│   │   │   ├── ClusterMarker.tsx
│   │   │   └── CreatePointModal.tsx
│   │   ├── points/
│   │   │   ├── PointList.tsx
│   │   │   ├── PointDetail.tsx
│   │   │   ├── PointForm.tsx
│   │   │   └── SearchFilter.tsx
│   │   ├── annotations/
│   │   │   ├── AnnotationList.tsx
│   │   │   ├── AnnotationUpload.tsx
│   │   │   ├── TextAnnotationPreview.tsx
│   │   │   ├── ImagePreview.tsx
│   │   │   └── DocumentPreview.tsx
│   │   ├── sharing/
│   │   │   ├── ShareModal.tsx
│   │   │   ├── PermissionSelector.tsx
│   │   │   └── SharedPointsList.tsx
│   │   └── common/
│   │       ├── ErrorBoundary.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ProgressBar.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePoints.ts
│   │   ├── useGeolocation.ts
│   │   └── useStorageQuota.ts
│   ├── store/
│   │   ├── authSlice.ts
│   │   ├── pointsSlice.ts
│   │   └── store.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── exportHelpers.ts
│   └── types/
│       ├── auth.ts
│       ├── point.ts
│       ├── annotation.ts
│       └── api.ts
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/

.github/
└── copilot-instructions.md  # Agent context file
```

**Structure Decision**: Web application with separate backend and frontend directories. Backend follows Django app-based modular structure with clear separation of concerns (authentication, points, annotations, sharing, trash, export/import). Frontend uses React component-based architecture with feature-folder organization. Both follow constitution's English-only code/comments requirement.

## Phase 0: Outline & Research

**Goal**: Resolve all technical uncertainties and document technology choices before design phase.

**Execution**:
1. **Identified Research Topics** (from Technical Context):
   - Backend framework selection (Django vs FastAPI vs Flask)
   - Frontend framework selection (React vs Vue vs Svelte)
   - Database choice for geospatial data (PostgreSQL+PostGIS vs MongoDB)
   - Authentication strategy (JWT vs Session-based)
   - File storage approach (Local vs S3-compatible)
   - Mapping library selection (Leaflet vs MapLibre vs OpenLayers)
   - Rich text editor (Quill vs TinyMCE vs Slate)
   - File preview implementation (native browser vs external libraries)
   - Import/Export format handling (python libraries for GeoJSON/GPX/KML/CSV)
   - Testing frameworks (pytest+Vitest+Playwright chosen)

2. **Research Process**:
   - For each topic: Evaluated 2-3 alternatives
   - Assessed based on: learning curve, ecosystem, performance, PostgreSQL integration, geospatial support
   - Documented decision rationale in research.md

3. **Key Decisions Made**:
   - **Backend**: Django + Django REST Framework (mature, excellent PostgreSQL/PostGIS support, built-in admin)
   - **Frontend**: React + Vite (large ecosystem, excellent TypeScript support, fast dev experience)
   - **Database**: PostgreSQL 15+ with PostGIS (native geospatial operations, ACID compliance, mature)
   - **Auth**: JWT via djangorestframework-simplejwt (stateless, scalable, refresh tokens)
   - **Storage**: Django FileField with S3-compatible backend (abstraction, dev/prod parity)
   - **Mapping**: Leaflet 1.9+ (lightweight, extensive plugin ecosystem, simple API)
   - **Rich Text**: Quill (WYSIWYG, emoji support, clean HTML output)
   - **File Preview**: Native browser (images/PDFs) + react-pdf (enhanced PDF viewing)
   - **Import/Export**: GeoPandas + gpxpy + simplekml + csv (standard libraries, well-tested)
   - **Testing**: pytest + pytest-django (backend), Vitest + React Testing Library (frontend), Playwright (E2E)

**Output**: ✅ research.md complete with 9 major technical decisions documented

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Load Template**: Use `.specify/templates/tasks-template.md` as base structure
2. **Extract Tasks from Design Artifacts**:
   - **From data-model.md**:
     - Django model creation tasks (7 entities)
     - Migration tasks (PostGIS setup, indexes)
     - Model validation test tasks
   - **From contracts/*.yaml**:
     - Contract test tasks for each endpoint (28 endpoints total)
     - Serializer creation tasks
     - View/viewset implementation tasks
     - URL routing tasks
   - **From quickstart.md**:
     - Integration test tasks (8 scenarios)
     - E2E test tasks (critical user journeys)
   - **Infrastructure Tasks**:
     - Django project setup (settings, apps, middleware)
     - React project setup (Vite, TypeScript, Leaflet)
     - CI/CD configuration (GitHub Actions, pytest, Vitest)
     - Deployment configuration (Docker, WSGI, static files)

3. **Task Ordering Strategy** (TDD + Dependency):
   ```
   Phase A: Foundation [P = parallel execution possible]
     1. Django project setup [P]
     2. React project setup [P]
     3. PostgreSQL + PostGIS setup
     4. User model + authentication (tests first) [CRITICAL PATH]

   Phase B: Core Data Layer (depends on Phase A)
     5. GPSPoint model + tests [CRITICAL PATH]
     6. Tag model + tests [P]
     7. Annotation model + tests [P]
     8. Share model + tests [P]
     9. Trash model + tests [P]

   Phase C: API Contracts (depends on Phase B)
     10-15. Auth endpoints + contract tests [P after model ready]
     16-22. Points endpoints + contract tests [CRITICAL PATH]
     23-29. Annotations endpoints + contract tests [P]
     30-36. Sharing endpoints + contract tests [P]
     37-42. Export/Import endpoints + contract tests [P]

   Phase D: Business Logic (depends on Phase C)
     43. Editing lock service + tests
     44. Storage quota service + tests [CRITICAL PATH]
     45. Permission checking service + tests
     46. Email invitation service + tests
     47. File upload/preview service + tests
     48. GeoJSON/GPX/KML/CSV parsers + tests

   Phase E: Frontend Core (depends on Phase C contracts)
     49. React Router + auth context [CRITICAL PATH]
     50. Leaflet map component + tests
     51. Point creation/editing UI + tests
     52. Annotation upload UI + tests
     53. Sharing UI + tests

   Phase F: Integration & Performance
     54. Integration test scenarios (quickstart.md)
     55. E2E tests (Playwright)
     56. Performance tests (k6 load testing)
     57. Accessibility audit (WCAG 2.1 AA)

   Phase G: Deployment
     58. Docker configuration
     59. CI/CD pipeline (GitHub Actions)
     60. Production environment setup
   ```

4. **Task Attributes**:
   - **[P]**: Parallelizable (no blocking dependencies)
   - **[CRITICAL PATH]**: Blocks multiple downstream tasks
   - **[TDD]**: Test-first development required (all tasks unless infrastructure)
   - **Estimated LOC**: Based on similar features
   - **Constitution Check**: Explicit check for each task

**Estimated Output**:
- **60-70 tasks** total
- **~40% parallelizable** (marked [P])
- **TDD order enforced**: All contract tests before implementations
- **Dependency chain**: Models → Services → Views → UI
- **Critical path**: User auth → Points → Storage quota → Sharing

**Task File Structure** (tasks.md):
```markdown
# Task List: GeoAnnotator Web Application

## Complexity Summary
Total Estimated Tasks: 65
Parallelizable: 26 tasks ([P] marked)
Critical Path Length: 18 tasks
Estimated Total LOC: ~15,000-20,000

## Phase A: Foundation (Tasks 1-4)
### Task 1: Django Project Setup [P]
**Type**: Infrastructure
**Description**: Initialize Django 4.2+ project with PostgreSQL/PostGIS configuration
**Files**: backend/config/, backend/manage.py, requirements/base.txt
**Estimated LOC**: 150
**Dependencies**: None
**Acceptance Criteria**:
- [x] Django project created with config/ directory
- [x] PostgreSQL + PostGIS connection configured
- [x] Settings split (base/development/production)
- [x] pytest + pytest-django configured
**Constitution Check**: ✅ Infrastructure task (no code quality checks yet)

### Task 2: React Project Setup [P]
...

## Phase B: Core Data Layer (Tasks 5-9)
### Task 5: User Model + Authentication Tests [CRITICAL PATH] [TDD]
...
```

**IMPORTANT**:
- This phase is **described** by /plan command
- This phase is **executed** by /tasks command
- The /plan command STOPS HERE and outputs this plan.md file

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ No Constitution violations identified

No complexity deviations documented. All design decisions align with constitutional principles:
- Code quality: Django/React follow linting standards (Black, ESLint)
- Testing: TDD approach with ≥80% coverage target
- UX consistency: English-only UI, WCAG 2.1 AA accessibility
- Performance: Explicit targets (<200ms API p95, <1.5s map render)

If complexity issues arise during implementation, document here:
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none currently)* | - | - |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - ✅ research.md created
- [x] Phase 1: Design complete (/plan command) - ✅ data-model.md, contracts/*.yaml, quickstart.md, agent file
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - ✅ Approach documented above
- [x] Phase 3: Tasks generated (/tasks command) - ✅ tasks.md with 114 ordered tasks created
- [ ] Phase 4: Implementation complete - **NEXT STEP**: Execute tasks T001-T114
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: ✅ PASS (all 4 principles verified)
- [x] Post-Design Constitution Check: ✅ PASS (no violations in design artifacts)
- [x] All NEEDS CLARIFICATION resolved (no markers found in spec.md)
- [x] Complexity deviations documented (none - clean design)

**Artifacts Generated**:
- ✅ specs/001-build-a-web/plan.md (this file)
- ✅ specs/001-build-a-web/research.md (9 major technical decisions)
- ✅ specs/001-build-a-web/data-model.md (7 entities, validation, indexes)
- ✅ specs/001-build-a-web/contracts/auth.yaml (5 endpoints)
- ✅ specs/001-build-a-web/contracts/points.yaml (6 endpoints + tags)
- ✅ specs/001-build-a-web/contracts/annotations.yaml (6 endpoints)
- ✅ specs/001-build-a-web/contracts/sharing.yaml (6 endpoints)
- ✅ specs/001-build-a-web/contracts/export-import.yaml (5 endpoints + trash)
- ✅ specs/001-build-a-web/quickstart.md (8 test scenarios, 60+ test steps)
- ✅ .github/copilot-instructions.md (agent context)
- ✅ specs/001-build-a-web/tasks.md (114 ordered, testable tasks with TDD workflow)

**Next Command**: Execute tasks T001-T114 following TDD workflow (contract tests → implementation → integration tests)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
