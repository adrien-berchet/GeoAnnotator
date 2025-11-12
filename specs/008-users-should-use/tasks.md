# Tasks: User Pseudonyms and Account Management

**Input**: Design documents from `/specs/008-users-should-use/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Progress**: 75 of 84 tasks complete (89%) - **Phase 3.6 COMPLETE ✅**

## Execution Flow (main)
```
1. Load plan.md from feature directory ✅
   → Tech stack: Python 3.11+ (backend), TypeScript 5.9.3 (frontend)
   → Libraries: Django REST Framework, React 19.1.1, Vite 7.1.7
   → Structure: Web app (backend/ + frontend/)
2. Load design documents ✅
   → data-model.md: 4 entities (User, EmailChangeConfirmation, AccountLog, Share)
   → contracts/: 8 API endpoints
   → research.md: 10 technical decisions
   → quickstart.md: 8 test scenarios
3. Generate tasks by category ✅
   → Setup: Dependencies, migrations, email configuration
   → Tests: 8 contract tests, 6 integration tests
   → Core: Models, services, API endpoints
   → Integration: Signals, Celery tasks, email templates
   → Polish: Frontend components, accessibility, performance
4. Apply task rules ✅
   → Different files = [P] parallel execution
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T056) ✅
6. Generate dependency graph ✅
7. Create parallel execution examples ✅
8. Validate task completeness ✅
   → All 8 contracts have tests ✅
   → All 4 entities have models ✅
   → All endpoints implemented ✅
9. Return: SUCCESS (56 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/apps/users/`, `backend/tests/`
- **Frontend**: `frontend/src/components/Account/`, `frontend/tests/`
- Follows web application structure from plan.md

---

## Phase 3.1: Setup ✅ COMPLETE

### Backend Dependencies
- [x] **T001** Add `django-fernet-fields` to `backend/requirements/base.txt` for email encryption
- [x] **T002** Configure `FERNET_KEY` environment variable in `backend/config/settings/base.py` and `.env.example`
- [x] **T003** [P] Configure Django REST Framework rate limiting in `backend/config/settings/base.py` (10 req/min account ops, 3 req/h emails)
- [x] **T004** [P] Update linting configuration to enforce code quality standards (Ruff for Python, ESLint for TypeScript)

### Database Migrations
- [x] **T005** Create migration to add `pseudonym` field (max 100 chars) to User model in `backend/apps/authentication/migrations/0004_add_pseudonym.py`
- [x] **T006** Create migration to add `deleted_at` (nullable DateTime) and `pending_email` (encrypted) fields to User model in `backend/apps/authentication/migrations/0005_add_deleted_at_and_pending_email.py`
- [x] **T007** Create migration to convert User `email` field to `EncryptedEmailField` in `backend/apps/authentication/migrations/0006_encrypt_email.py`
- [x] **T008** Create migration for `EmailChangeConfirmation` model in `backend/apps/authentication/migrations/0007_email_change_confirmation.py`
- [x] **T009** Create migration for `AccountLog` model in `backend/apps/authentication/migrations/0008_account_log.py`
- [x] **T010** Create migration to add `is_active` boolean field to Share model (SKIPPED - field already exists)
- [x] **T011** Create migration to add database indexes (pseudonym lowercase unique, deleted_at partial, is_active partial) in `backend/apps/authentication/migrations/0009_add_indexes.py`

### Email Configuration
- [x] **T012** Create email template for email change confirmation in `backend/apps/authentication/templates/emails/confirm_email_change.html`
- [x] **T013** Create email template for account deletion warning in `backend/apps/authentication/templates/emails/confirm_account_deletion.html`

---

## Phase 3.2: Tests First (TDD) ✅ COMPLETE

**All tests created retroactively to validate existing implementation**

### Backend Contract Tests (API Endpoints)
- [x] **T014** [P] Contract test GET `/api/account/` in `backend/apps/tests/contract/test_account_get.py` (7 test methods: authentication, response schema, email decryption, deleted user handling)
- [x] **T015** [P] Contract test PATCH `/api/account/` in `backend/apps/tests/contract/test_account_update.py` (11 test methods: pseudonym validation, uniqueness, special characters, logging)
- [x] **T016** [P] Contract test POST `/api/account/change-email/` in `backend/apps/tests/contract/test_email_change.py` (8 test methods: email validation, duplicate detection, confirmation records)
- [x] **T017** [P] Contract test POST `/api/account/confirm-email/` in `backend/apps/tests/contract/test_email_confirm.py` (7 test methods: token validation, expiry, authorization, email update)
- [x] **T018** [P] Contract test POST `/api/account/change-password/` in `backend/apps/tests/contract/test_password_change.py` (8 test methods: old password verification, strength validation, logging)
- [x] **T019** [P] Contract test DELETE `/api/account/` in `backend/apps/tests/contract/test_account_delete.py` (5 test methods: deletion request, warning message, pre-confirmation state)
- [x] **T020** [P] Contract test POST `/api/account/confirm-delete/` in `backend/apps/tests/contract/test_account_delete_confirm.py` (10 test methods: token validation, soft delete, share deactivation)
- [x] **T021** [P] Contract test POST `/api/account/validate-pseudonym/` in `backend/apps/tests/contract/test_pseudonym_validate.py` (10 test methods: validation rules, uniqueness, no side effects)

### Backend Unit Tests
- [x] **T022** [P] Unit test pseudonym validation logic in `backend/apps/tests/unit/test_pseudonym_validation.py` (15 test methods: regex, length, characters, uniqueness, case-insensitivity)
- [x] **T023** [P] Unit test email encryption/decryption in `backend/apps/tests/unit/test_email_encryption.py` (9 test methods: Fernet encryption/decryption, roundtrip, special characters)
- [x] **T024** [P] Unit test soft delete behavior in `backend/apps/tests/unit/test_soft_delete.py` (17 test methods: deleted_at, active/objects managers, filtering, restoration)

### Backend Integration Tests (User Stories from Quickstart)
- [x] **T025** [P] Integration test pseudonym creation flow in `backend/apps/tests/integration/test_pseudonym_creation.py` (8 test methods: new user → set pseudonym → menu display)
- [x] **T026** [P] Integration test pseudonym validation scenarios in `backend/apps/tests/integration/test_pseudonym_validation.py` (14 test methods: spaces, length, duplicates, special chars in complete flow)
- [x] **T027** [P] Integration test email change confirmation flow in `backend/apps/tests/integration/test_email_change_flow.py` (10 test methods: request → email → confirm → email updated)
- [x] **T028** [P] Integration test password change verification flow in `backend/apps/tests/integration/test_password_change_flow.py` (11 test methods: old password verification → update → confirmation)
- [x] **T029** [P] Integration test account deletion soft delete flow in `backend/apps/tests/integration/test_account_deletion_flow.py` (14 test methods: request → confirm → soft delete → 30-day cleanup)
- [x] **T030** [P] Integration test pseudonym display in sharing in `backend/apps/tests/integration/test_pseudonym_sharing.py` (13 test methods: pseudonym display in shares instead of email)

---

## Phase 3.3: Core Implementation ✅ COMPLETE

### Backend Models
- [x] **T031** [P] Update User model in `backend/apps/authentication/models.py` (add pseudonym, deleted_at, pending_email fields, EncryptedEmailField for email)
- [x] **T032** [P] Create EmailChangeConfirmation model in `backend/apps/authentication/models.py` (token, new_email, expires_at, confirmed_at)
- [x] **T033** [P] Create AccountLog model in `backend/apps/authentication/models.py` (operation enum, user FK, timestamp, details JSONField)
- [x] **T034** [P] Add ActiveUserManager to User model in `backend/apps/authentication/models.py` (filter deleted_at__isnull=True)

### Backend Services
- [x] **T035** Implement pseudonym validation service in `backend/apps/authentication/services.py` (validate_pseudonym: regex, length, uniqueness check)
- [x] **T036** Implement EmailChangeTokenGenerator in `backend/apps/authentication/services.py` (HMAC-based, 30-minute expiry)
- [x] **T037** Implement AccountDeletionTokenGenerator in `backend/apps/authentication/services.py` (similar to email change token)
- [x] **T038** Implement email sending service in `backend/apps/authentication/services.py` (send_email_change_confirmation, send_deletion_confirmation)
- [x] **T039** Implement soft delete service in `backend/apps/authentication/services.py` (set_deleted, unshare_user_content)

### Backend Serializers
- [x] **T040** Create AccountSerializer in `backend/apps/authentication/serializers.py` (pseudonym, email read-only, exclude password/deleted_at)
- [x] **T041** Create PseudonymUpdateSerializer in `backend/apps/authentication/serializers.py` (validate pseudonym rules, uniqueness)
- [x] **T042** Create EmailChangeSerializer in `backend/apps/authentication/serializers.py` (validate new_email, check not in use)
- [x] **T043** Create EmailConfirmSerializer in `backend/apps/authentication/serializers.py` (validate token, update email)
- [x] **T044** Create PasswordChangeSerializer in `backend/apps/authentication/serializers.py` (validate old_password, set new_password)

### Backend Views (API Endpoints)
- [x] **T045** Implement GET `/api/account/` view in `backend/apps/authentication/views.py` (AccountRetrieveAPIView)
- [x] **T046** Implement PATCH `/api/account/update/` view in `backend/apps/authentication/views.py` (AccountUpdateAPIView, pseudonym update, log operation)
- [x] **T047** Implement POST `/api/account/change-email/` view in `backend/apps/authentication/views.py` (create token, send email, log request)
- [x] **T048** Implement POST `/api/account/confirm-email/` view in `backend/apps/authentication/views.py` (validate token, update email, log confirmation)
- [x] **T049** Implement POST `/api/account/change-password/` view in `backend/apps/authentication/views.py` (verify old password, set new, log)
- [x] **T050** Implement DELETE `/api/account/delete/` view in `backend/apps/authentication/views.py` (send deletion confirmation email, log request)
- [x] **T051** Implement POST `/api/account/confirm-delete/` view in `backend/apps/authentication/views.py` (validate token, soft delete, unshare, log deletion)
- [x] **T052** Implement POST `/api/account/validate-pseudonym/` view in `backend/apps/authentication/views.py` (validation endpoint for frontend)

### Backend URLs
- [x] **T053** Register all account endpoints in `backend/apps/authentication/urls.py` (8 URL patterns)

---

## Phase 3.4: Integration ✅ COMPLETE

### Backend Infrastructure
- [x] **T054** Create Django signal for unsharing on delete in `backend/apps/sharing/signals.py` (pre_save receiver, set is_active=False when deleted_at is set)
- [x] **T055** Create Celery periodic task for cleanup_deleted_users in `backend/apps/authentication/tasks.py` (delete users where deleted_at < now() - 30 days, run daily at 2AM)
- [x] **T056** Update Share model queryset manager in `backend/apps/sharing/models.py` (ActiveShareManager filters is_active=True by default)

### Additional Infrastructure Completed
- [x] Created Celery configuration in `backend/config/celery.py` with Beat schedule
- [x] Registered Celery app in `backend/config/__init__.py`
- [x] Added Celery dependencies (celery>=5.3, redis>=5.0) to requirements
- [x] Configured Celery settings in `backend/config/settings/base.py`
- [x] Updated `.env.example` with Celery configuration

---

## Phase 3.5: Frontend Components ✅ COMPLETE

### Frontend Services
- [x] **T057** Implement accountService.ts in `frontend/src/api/account.ts` (API client for all 8 endpoints)
- [x] **T058** Implement useAccount hook in `frontend/src/hooks/useAccount.ts` (account management operations with state)
- [x] **T059** Update user context in `frontend/src/types/auth.ts` (expose pseudonym in User type)

### Frontend Components
- [x] **T060** Create AccountPage in `frontend/src/pages/AccountPage.tsx` (account management page with all sections)
- [x] **T061** [P] Implement PseudonymField component in `frontend/src/components/account/PseudonymField.tsx` (inline validation, debounced API check, error display)
- [x] **T062** [P] Implement EmailChangeForm component in `frontend/src/components/account/EmailChangeForm.tsx` (request change, show confirmation message, handle errors)
- [x] **T063** [P] Implement PasswordChangeForm component in `frontend/src/components/account/PasswordChangeForm.tsx` (old password field, new password, validation)
- [x] **T064** [P] Implement DeleteAccountButton component in `frontend/src/components/account/DeleteAccountButton.tsx` (warning modal, confirmation flow)
- [x] **T065** Update menu bar to display pseudonym in `frontend/src/components/layout/Navbar.tsx` (show account.pseudonym instead of account.email)
- [x] **T066** Update sharing components to display pseudonym in `frontend/src/components/sharing/SharedPointsList.tsx` (show recipient.pseudonym with fallback to email)

### Frontend Routes
- [x] **T067** Add email confirmation route in `frontend/src/pages/EmailConfirmPage.tsx` (/account/confirm-email route handler)
- [x] **T068** Add account deletion confirmation route in `frontend/src/pages/AccountDeleteConfirmPage.tsx` (/account/confirm-delete route handler)
- [x] **T069** Update navigation to use /account instead of /profile in `frontend/src/routes.tsx` (added /account route)

---

## Phase 3.6: Frontend Tests

### Frontend Component Tests
- [x] **T070** [P] Component test AccountPage in `frontend/tests/components/Account/AccountPage.test.tsx` (8 tests: renders all sections, accessibility, semantic HTML)
- [x] **T071** [P] Component test PseudonymField in `frontend/tests/components/Account/PseudonymField.test.tsx` (11 tests: validation display, debounce, error states, update workflow)
- [x] **T072** [P] Component test EmailChangeForm in `frontend/tests/components/Account/EmailChangeForm.test.tsx` (11 tests: submit, success message, errors, validation)
- [x] **T073** [P] Component test PasswordChangeForm in `frontend/tests/components/Account/PasswordChangeForm.test.tsx` (12 tests: old password required, validation, show/hide)
- [x] **T074** [P] Component test DeleteAccountButton in `frontend/tests/components/Account/DeleteAccountButton.test.tsx` (15 tests: warning modal, confirmation, accessibility)

### Frontend Integration Tests
- [x] **T075** Integration test account management flow in `frontend/tests/integration/account-management.test.tsx` (9 tests: full user journey - create pseudonym, change email, change password, delete account)

---

## Phase 3.7: Polish

### Accessibility & Performance
- [ ] **T076** Accessibility audit for Account page in `frontend/src/components/Account/` (WCAG 2.1 Level AA: keyboard nav, screen reader, contrast, ARIA labels)
- [ ] **T077** Responsive design testing for Account page (320px-2560px viewports, verify layout, buttons, forms)
- [ ] **T078** Performance benchmarking for API endpoints (verify <200ms p95 for validation, <500ms p95 for updates, measure with Django Debug Toolbar)
- [ ] **T079** Database query optimization (verify indexes used, no N+1 queries, check with EXPLAIN ANALYZE)

### Documentation
- [ ] **T080** [P] Update API documentation in `docs/api.md` (document all 8 new endpoints with examples)
- [ ] **T081** [P] Update user documentation in `docs/account-management.md` (explain pseudonym, email change, password change, account deletion flows)

### Cleanup & Refactoring
- [ ] **T082** Remove deprecated ProfilePage component from `frontend/src/components/Profile/` (ensure all references updated)
- [ ] **T083** Refactor complex validation logic (ensure functions <50 lines, complexity <10 per constitution)
- [ ] **T084** Run manual testing from `specs/008-users-should-use/quickstart.md` (execute all 8 test scenarios, verify English error messages)

---

## Dependencies

### Phase Dependencies
```
Phase 3.1 (Setup) blocks all other phases
Phase 3.2 (Tests) blocks Phase 3.3 (Implementation)
Phase 3.3 (Backend Core) blocks Phase 3.4 (Integration) and Phase 3.5 (Frontend)
Phase 3.4 (Integration) can run parallel with Phase 3.5 (Frontend)
Phase 3.6 (Frontend Tests) requires Phase 3.5 (Frontend Components)
Phase 3.7 (Polish) requires all previous phases
```

### Specific Task Dependencies
```
T001-T013 (Setup) must complete before any other tasks
T014-T030 (Tests) must complete before T031-T053 (Implementation)
T031-T034 (Models) block T035-T039 (Services)
T035-T039 (Services) block T040-T044 (Serializers)
T040-T044 (Serializers) block T045-T052 (Views)
T045-T052 (Views) require T053 (URLs)
T054-T056 (Integration) require T031-T034 (Models)
T057-T059 (Frontend Services) require T045-T053 (Backend API)
T060-T069 (Frontend Components) require T057-T059 (Frontend Services)
T070-T075 (Frontend Tests) require T060-T069 (Frontend Components)
T076-T084 (Polish) require all implementation complete
```

---

## Parallel Execution Examples

### Parallel Group 1: Backend Contract Tests (After T013)
```bash
# Launch T014-T021 together (8 contract tests, different files):
Task: "Contract test GET /api/account/ in backend/tests/contract/test_account_get.py"
Task: "Contract test PATCH /api/account/ in backend/tests/contract/test_account_update.py"
Task: "Contract test POST /api/account/change-email/ in backend/tests/contract/test_email_change.py"
Task: "Contract test POST /api/account/confirm-email/ in backend/tests/contract/test_email_confirm.py"
Task: "Contract test POST /api/account/change-password/ in backend/tests/contract/test_password_change.py"
Task: "Contract test DELETE /api/account/ in backend/tests/contract/test_account_delete.py"
Task: "Contract test POST /api/account/confirm-delete/ in backend/tests/contract/test_account_delete_confirm.py"
Task: "Contract test POST /api/account/validate-pseudonym/ in backend/tests/contract/test_pseudonym_validate.py"
```

### Parallel Group 2: Backend Unit Tests (After T021)
```bash
# Launch T022-T024 together (3 unit tests, different files):
Task: "Unit test pseudonym validation in backend/tests/unit/test_pseudonym_validation.py"
Task: "Unit test email encryption in backend/tests/unit/test_email_encryption.py"
Task: "Unit test soft delete in backend/tests/unit/test_soft_delete.py"
```

### Parallel Group 3: Backend Integration Tests (After T024)
```bash
# Launch T025-T030 together (6 integration tests, different files):
Task: "Integration test pseudonym creation in backend/tests/integration/test_pseudonym_creation.py"
Task: "Integration test pseudonym validation in backend/tests/integration/test_pseudonym_validation.py"
Task: "Integration test email change flow in backend/tests/integration/test_email_change_flow.py"
Task: "Integration test password change flow in backend/tests/integration/test_password_change_flow.py"
Task: "Integration test account deletion flow in backend/tests/integration/test_account_deletion_flow.py"
Task: "Integration test pseudonym sharing in backend/tests/integration/test_pseudonym_sharing.py"
```

### Parallel Group 4: Backend Models (After T030)
```bash
# Launch T031-T034 together (4 model tasks, different sections of models.py):
# NOTE: While same file, these are independent model classes that can be written in parallel
Task: "Update User model in backend/apps/users/models.py"
Task: "Create EmailChangeConfirmation model in backend/apps/users/models.py"
Task: "Create AccountLog model in backend/apps/users/models.py"
Task: "Add ActiveUserManager in backend/apps/users/models.py"
```

### Parallel Group 5: Frontend Components (After T059)
```bash
# Launch T061-T064 together (4 components, different files):
Task: "Implement PseudonymField in frontend/src/components/Account/PseudonymField.tsx"
Task: "Implement EmailChangeForm in frontend/src/components/Account/EmailChangeForm.tsx"
Task: "Implement PasswordChangeForm in frontend/src/components/Account/PasswordChangeForm.tsx"
Task: "Implement DeleteAccountButton in frontend/src/components/Account/DeleteAccountButton.tsx"
```

### Parallel Group 6: Frontend Component Tests (After T069)
```bash
# Launch T070-T074 together (5 component tests, different files):
Task: "Component test AccountPage in frontend/tests/components/Account/AccountPage.test.tsx"
Task: "Component test PseudonymField in frontend/tests/components/Account/PseudonymField.test.tsx"
Task: "Component test EmailChangeForm in frontend/tests/components/Account/EmailChangeForm.test.tsx"
Task: "Component test PasswordChangeForm in frontend/tests/components/Account/PasswordChangeForm.test.tsx"
Task: "Component test DeleteAccountButton in frontend/tests/components/Account/DeleteAccountButton.test.tsx"
```

### Parallel Group 7: Documentation (After T079)
```bash
# Launch T080-T081 together (2 doc tasks, different files):
Task: "Update API docs in docs/api.md"
Task: "Update user docs in docs/account-management.md"
```

---

## Validation Checklist

**GATE: Checked before task execution begins**

- [x] All 8 contracts have corresponding tests (T014-T021)
- [x] All 4 entities have model tasks (T031-T034)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (verified file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task (verified)
- [x] TDD workflow enforced (tests must fail before implementation)
- [x] Performance targets defined (T078: <200ms p95 validation, <500ms p95 updates)
- [x] Accessibility requirements included (T076: WCAG 2.1 Level AA)
- [x] Documentation in English (T080-T081, T084)
- [x] Constitution compliance verified (code quality, testing, UX consistency)

---

## Progress Tracking

**Total Tasks**: 84
**Completed**: 69 (82%)
**Remaining**: 15 (18%)
**Estimated Duration**: 3-4 weeks (full-time developer)

### Task Breakdown by Category:
- Setup: 13 tasks ✅ COMPLETE (T001-T013)
- Backend Tests: 17 tasks ✅ COMPLETE (T014-T030)
- Backend Implementation: 23 tasks ✅ COMPLETE (T031-T053)
- Backend Integration: 3 tasks ✅ COMPLETE (T054-T056)
- Frontend Services: 3 tasks ✅ COMPLETE (T057-T059)
- Frontend Components: 10 tasks ✅ COMPLETE (T060-T069)
- Frontend Tests: 6 tasks ✅ COMPLETE (T070-T075) - **66 tests total**
- Polish: 9 tasks - 0 complete (T076-T084)

### Parallel Execution Opportunities:
- 8 contract tests (T014-T021)
- 3 unit tests (T022-T024)
- 6 integration tests (T025-T030)
- 4 models (T031-T034)
- 4 frontend components (T061-T064)
- 5 frontend component tests (T070-T074)
- 2 documentation tasks (T080-T081)

**Total Parallel Tasks**: 32 out of 84 (38% can run in parallel)

---

## Notes

- **[P] marker**: Tasks marked [P] operate on different files and have no dependencies, can be executed simultaneously
- **TDD enforcement**: Phase 3.2 (tests) MUST complete and FAIL before Phase 3.3 (implementation) begins
- **Commit frequency**: Commit after each task completion for granular history
- **Test coverage**: Target ≥80% general, ≥95% for authentication, email, and deletion critical paths
- **Performance monitoring**: Use Django Debug Toolbar (backend) and Lighthouse (frontend) during T078
- **Accessibility tools**: Use axe DevTools, NVDA/JAWS screen readers during T076
- **English enforcement**: All error messages, documentation, and UI text must be in English (US) per constitution

---

**Ready for execution**: All 84 tasks defined with clear file paths, dependencies, and acceptance criteria.
