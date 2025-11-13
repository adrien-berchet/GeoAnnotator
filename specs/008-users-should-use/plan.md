
# Implementation Plan: User Pseudonyms and Account Management

**Branch**: `008-users-should-use` | **Date**: 2025-11-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-users-should-use/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement user pseudonym system to protect email privacy. Users create unique pseudonyms displayed throughout the application instead of email addresses. The Account page (renamed from Profile) enables management of pseudonym, email (with confirmation), password (with verification), and account deletion (with 30-day soft delete). Email addresses are encrypted in database but viewable in plain text by owners. Shared content is immediately unshared on account deletion with 30-day retention before permanent deletion.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5.9.3 (frontend)
**Primary Dependencies**: Django REST Framework (backend), React 19.1.1, Vite 7.1.7 (frontend)
**Storage**: PostgreSQL (email encryption, pseudonym uniqueness, soft delete tracking)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Linux server (backend), Web browsers (frontend)
**Project Type**: web (frontend + backend)
**Performance Goals**: <200ms p95 for pseudonym validation, <500ms p95 for account updates, email confirmation within 1 minute
**Constraints**: 30-minute email confirmation expiry, 30-day soft delete retention, <100 character pseudonym length, WCAG 2.1 Level AA compliance
**Scale/Scope**: All authenticated users, pseudonym uniqueness across entire user base, email encryption for all user records

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Code Quality Standards**:
- [x] Code will adhere to linting and type checking standards (Ruff for Python, ESLint for TypeScript)
- [x] All code will be documented in English with clear API descriptions (docstrings for Python, JSDoc for TypeScript)
- [x] Complexity limits will be respected (functions <50 lines, complexity <10)

**Testing Requirements**:
- [x] TDD approach planned (contract tests before implementation, user story tests before UI)
- [x] Coverage targets defined (≥80% general, ≥95% for auth/email/deletion critical paths)
- [x] Unit, integration, and E2E test types identified (unit: validation logic, integration: API contracts, E2E: account management flows)

**User Experience Consistency**:
- [x] All UI/UX elements designed in English (US) (Account page, error messages, validation warnings)
- [x] WCAG 2.1 Level AA accessibility considered (FR-030: keyboard navigation, screen reader support, 4.5:1 contrast)
- [x] Responsive design planned (320px-2560px viewports per FR-031)
- [x] Error messages planned with clear, actionable English text (pseudonym validation, email conflicts, password mismatch)

**Performance Requirements**:
- [x] API response time targets defined (<200ms p95 pseudonym validation, <500ms p95 account updates)
- [x] Resource efficiency targets set (email encryption overhead minimized, database indexing on pseudonym uniqueness)
- [x] Performance monitoring and load testing planned (log account operations per FR-029, measure email send latency)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── apps/
│   ├── users/
│   │   ├── models.py              # User model with pseudonym field, email encryption
│   │   ├── serializers.py         # Account management serializers
│   │   ├── views.py               # Account CRUD, email confirmation, password change
│   │   ├── services.py            # Email sending, pseudonym validation, soft delete
│   │   └── migrations/            # Add pseudonym field, email encryption, soft delete fields
│   └── sharing/
│       └── models.py               # Update to reference pseudonym, handle unsharing on delete
└── tests/
    ├── contract/                   # API contract tests
    │   ├── test_account_get.py
    │   ├── test_account_update.py
    │   ├── test_pseudonym_validate.py
    │   ├── test_email_change.py
    │   ├── test_password_change.py
    │   └── test_account_delete.py
    ├── integration/                # User story integration tests
    │   ├── test_pseudonym_creation.py
    │   ├── test_account_management.py
    │   └── test_account_deletion_flow.py
    └── unit/                       # Validation logic unit tests
        ├── test_pseudonym_validation.py
        ├── test_email_encryption.py
        └── test_soft_delete.py

frontend/
├── src/
│   ├── components/
│   │   └── Account/               # Renamed from Profile
│   │       ├── AccountPage.tsx
│   │       ├── PseudonymField.tsx
│   │       ├── EmailChangeForm.tsx
│   │       ├── PasswordChangeForm.tsx
│   │       └── DeleteAccountButton.tsx
│   ├── services/
│   │   └── accountService.ts      # API calls for account management
│   └── hooks/
│       └── useAccount.ts          # Account state management
└── tests/
    ├── components/
    │   └── Account/
    │       ├── AccountPage.test.tsx
    │       ├── PseudonymField.test.tsx
    │       ├── EmailChangeForm.test.tsx
    │       ├── PasswordChangeForm.test.tsx
    │       └── DeleteAccountButton.test.tsx
    └── integration/
        └── account-management.test.tsx
```

**Structure Decision**: Web application structure with frontend and backend. Backend uses Django app pattern under `apps/users/` for user account management and extends `apps/sharing/` for pseudonym display and unsharing logic. Frontend creates new `components/Account/` directory (renamed from Profile) with dedicated components for each account management feature. Testing follows TDD with contract tests defining API, integration tests validating user stories, and unit tests for validation logic.

## Phase 0: Outline & Research

**Status**: ✅ Complete

**Artifacts Generated**:
- `research.md`: All technical decisions documented
  - Email encryption strategy (Fernet via django-fernet-fields)
  - Pseudonym uniqueness enforcement (DB constraint + app validation)
  - Email confirmation token system (HMAC-based, 30-minute expiry)
  - Account soft delete strategy (deleted_at timestamp + cleanup task)
  - Pseudonym validation rules (regex, <100 chars, no spaces)
  - Password change verification (Django check_password)
  - Sharing content unsharing (Django signals)
  - Frontend pseudonym display (centralized account state)
  - Performance optimization (indexing, query optimization)
  - Accessibility implementation (ARIA, WCAG 2.1 AA)

**Key Research Findings**:
- No NEEDS CLARIFICATION items remain
- All dependencies identified (django-fernet-fields)
- Performance targets achievable with proper indexing
- Email confirmation flow follows Django best practices
- Soft delete pattern well-established in Django ecosystem

---

## Phase 1: Design & Contracts

**Status**: ✅ Complete

**Artifacts Generated**:

1. **data-model.md**: Complete entity definitions
   - User model extensions (pseudonym, deleted_at, pending_email, encrypted email)
   - EmailChangeConfirmation model (token, expiry, confirmation tracking)
   - AccountLog model (audit trail for all operations)
   - Share model modifications (is_active flag)
   - Database schema with indexes and constraints
   - Migration plan with 9 migrations

2. **contracts/account-api.md**: API specifications
   - 8 REST endpoints fully documented
   - Request/response schemas with examples
   - Validation rules and error responses
   - Side effects and audit logging
   - Rate limiting policies
   - Authentication requirements

3. **quickstart.md**: Acceptance test scenarios
   - 8 complete test scenarios covering all user stories
   - Manual testing steps with expected results
   - API verification commands
   - Database verification queries
   - Performance benchmarks
   - Accessibility and responsive design tests

4. **Agent context updated**: `.github/copilot-instructions.md`
   - Technologies added: Python 3.11+, TypeScript 5.9.3, Django REST Framework, React 19.1.1
   - Database: PostgreSQL with email encryption
   - Recent changes documented

**Design Decisions**:
- Web application structure (frontend + backend)
- Django app pattern under `apps/users/`
- React components under `components/Account/`
- TDD approach: contracts → tests → implementation
- Three-tier testing: unit, integration, E2E

**Constitution Re-Check**: ✅ PASS
- No complexity violations
- All quality standards met
- Performance targets defined
- Accessibility requirements planned
- TDD approach documented

---

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load base template**: `.specify/templates/tasks-template.md`

2. **Generate backend tasks from data model**:
   - Each new model (EmailChangeConfirmation, AccountLog) → model creation task [P]
   - User model migration → migration task
   - Share model update → migration task [P]
   - Email encryption setup → configuration task

3. **Generate API implementation tasks from contracts**:
   - Each endpoint in `contracts/account-api.md` → implementation task
   - Group related endpoints (change-email + confirm-email)
   - Services layer for business logic (pseudonym validation, email sending, soft delete)

4. **Generate test tasks (TDD order)**:
   - Contract tests before API implementation (8 contract test files)
   - Unit tests for validation logic (pseudonym, email encryption)
   - Integration tests for user stories (quickstart scenarios)
   - Each test file → separate task [P] (can run in parallel)

5. **Generate frontend tasks**:
   - AccountPage component (renamed from ProfilePage)
   - Form components (PseudonymField, EmailChangeForm, PasswordChangeForm, DeleteAccountButton)
   - Service layer (accountService.ts API calls)
   - State management (useAccount hook)
   - Component tests for each form [P]

6. **Generate infrastructure tasks**:
   - Email template creation (confirmation, deletion warning)
   - Celery task for cleanup_deleted_users
   - Database index creation scripts
   - Django signals for unsharing on delete

**Ordering Strategy**:

**Phase 1: Foundation** (Backend Models & Migrations)
1. Add django-fernet-fields dependency
2. Create User model migration (pseudonym, deleted_at, pending_email, encrypted email)
3. Create EmailChangeConfirmation model [P]
4. Create AccountLog model [P]
5. Update Share model (is_active field) [P]
6. Create database indexes
7. Configure email encryption keys

**Phase 2: Contract Tests** (TDD - Tests First)
8. Write contract test: GET /api/account/ [P]
9. Write contract test: PATCH /api/account/ [P]
10. Write contract test: POST /api/account/change-email/ [P]
11. Write contract test: POST /api/account/confirm-email/ [P]
12. Write contract test: POST /api/account/password-change/ [P]
13. Write contract test: DELETE /api/account/ [P]
14. Write contract test: POST /api/account/confirm-delete/ [P]
15. Write contract test: POST /api/account/validate-pseudonym/ [P]

**Phase 3: Backend Services** (Business Logic)
16. Implement pseudonym validation service
17. Implement email encryption/decryption service
18. Implement email change token generator
19. Implement deletion confirmation token generator
20. Implement email sending service (templates)

**Phase 4: Backend API** (Make Contract Tests Pass)
21. Implement GET /api/account/ view
22. Implement PATCH /api/account/ view (pseudonym update)
23. Implement POST /api/account/change-email/ view
24. Implement POST /api/account/confirm-email/ view
25. Implement POST /api/account/password-change/ view
26. Implement DELETE /api/account/ view
27. Implement POST /api/account/confirm-delete/ view
28. Implement POST /api/account/validate-pseudonym/ view

**Phase 5: Backend Infrastructure**
29. Create Django signal for unsharing on delete
30. Create Celery task for cleanup_deleted_users
31. Add AccountLog entries to all operations

**Phase 6: Frontend Services** (API Integration)
32. Implement accountService.ts (API client)
33. Implement useAccount hook (state management)
34. Update user context to expose pseudonym

**Phase 7: Frontend Components** (UI)
35. Rename ProfilePage to AccountPage
36. Implement PseudonymField component with validation
37. Implement EmailChangeForm component
38. Implement PasswordChangeForm component
39. Implement DeleteAccountButton component with warning
40. Update menu bar to display pseudonym
41. Update sharing components to display pseudonym

**Phase 8: Frontend Tests**
42. Write component test: AccountPage [P]
43. Write component test: PseudonymField [P]
44. Write component test: EmailChangeForm [P]
45. Write component test: PasswordChangeForm [P]
46. Write component test: DeleteAccountButton [P]

**Phase 9: Integration Tests** (User Stories from Quickstart)
47. Write integration test: Pseudonym creation flow
48. Write integration test: Pseudonym validation scenarios
49. Write integration test: Email change confirmation flow
50. Write integration test: Password change verification flow
51. Write integration test: Account deletion soft delete flow
52. Write integration test: Pseudonym display in sharing

**Phase 10: Accessibility & Performance**
53. Accessibility audit (WCAG 2.1 AA compliance)
54. Responsive design testing (320px-2560px)
55. Performance benchmarking (API response times)
56. Database query optimization

**Task Metadata**:
- Tasks marked [P] can run in parallel (independent files)
- Each task includes:
  - Clear acceptance criteria
  - Reference to spec/contract/quickstart
  - Estimated time (S/M/L)
  - Dependencies on prior tasks
- Total estimated tasks: ~56
- Critical path: Backend models → Contract tests → API implementation → Frontend components
- Parallelization opportunities: Contract tests (8 parallel), Component tests (5 parallel), Models (3 parallel)

**Estimated Output**: 56 numbered, ordered tasks in tasks.md with [P] markers for parallel execution

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

**No Constitution Violations**

All implementation decisions align with constitutional principles:
- Code quality standards: Linting, type checking, documentation planned
- Testing requirements: TDD approach with ≥80% coverage (≥95% for auth/email/deletion critical paths)
- User experience: WCAG 2.1 AA compliance, responsive design, English-first
- Performance: <200ms p95 validation, <500ms p95 updates, indexed database queries
- Language: All code, docs, and UI in English (US)

**Complexity Justifications**: None needed

---

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md created
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, agent context updated
- [x] Phase 2: Task planning complete (/plan command - approach described, ready for /tasks)
- [x] Phase 3: Tasks generated (/tasks command) - tasks.md created with 84 tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (all standards met, no violations)
- [x] Post-Design Constitution Check: PASS (no new violations introduced)
- [x] All NEEDS CLARIFICATION resolved (none remaining)
- [x] Complexity deviations documented (none needed)

**Artifacts Generated**:
- ✅ `/specs/008-users-should-use/research.md` (10 research topics, all decisions documented)
- ✅ `/specs/008-users-should-use/data-model.md` (4 entities, schema, migrations)
- ✅ `/specs/008-users-should-use/contracts/account-api.md` (8 endpoints, fully specified)
- ✅ `/specs/008-users-should-use/quickstart.md` (8 test scenarios, manual + API verification)
- ✅ `/.github/copilot-instructions.md` (updated with new tech stack)
- ✅ `/specs/008-users-should-use/tasks.md` (84 tasks, fully ordered with dependencies and parallel execution)

**Ready for Next Phase**: Implementation (execute tasks.md following TDD workflow)

---
*Based on Constitution v1.0.1 - See `.specify/memory/constitution.md`*
