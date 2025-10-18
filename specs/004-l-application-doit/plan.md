
# Implementation Plan: Show Device Position on Map

**Branch**: `004-l-application-doit` | **Date**: 2025-10-19 | **Spec**: [/specs/004-l-application-doit/spec.md]
**Input**: Feature specification from `/specs/004-l-application-doit/spec.md`

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
Primary requirement: The application must retrieve the device’s current position and display it on the map with a blue dot, updating in real time. If the position is unavailable, the user is notified. The user can recenter the map on their position and create a new point at their location by clicking the blue dot.
Technical approach: Use browser geolocation APIs in the frontend (React/Leaflet), update the map marker in real time, and trigger UI flows for recentering and point creation. Handle permission and error states with user notifications.

## Technical Context
**Language/Version**: TypeScript 5.x (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 19.1.1, Leaflet 1.9.4, Django REST Framework
**Storage**: N/A (feature is frontend only)
**Testing**: Vitest (frontend), pytest (backend)
**Target Platform**: Web (desktop/mobile browsers)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Blue dot position update latency <500ms, UI response <200ms
**Constraints**: Must work on all major browsers, handle permission denial gracefully, maintain accessibility (WCAG 2.1 AA)
**Scale/Scope**: 1-10k concurrent users, single map view per session

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Code Quality Standards**:
- [x] Code will adhere to linting and type checking standards
- [x] All code will be documented in English with clear API descriptions
- [x] Complexity limits will be respected (functions <50 lines, complexity <10)

**Testing Requirements**:
- [x] TDD approach planned (tests before implementation)
- [x] Coverage targets defined (≥80% general, ≥95% critical paths)
- [x] Unit, integration, and E2E test types identified

**User Experience Consistency**:
- [x] All UI/UX elements designed in English (US)
- [x] WCAG 2.1 Level AA accessibility considered
- [x] Responsive design planned (320px-2560px viewports)
- [x] Error messages planned with clear, actionable English text

**Performance Requirements**:
- [x] API response time targets defined (<200ms p95 reads, <500ms p95 writes)
- [x] Resource efficiency targets set (bundle size <300KB, memory <512MB)
- [x] Performance monitoring and load testing planned

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

tests/
ios/ or android/
### Source Code (repository root)
```
backend/
├── apps/
│   ├── annotations/
│   ├── authentication/
│   ├── export_import/
│   ├── points/
│   ├── settings/
│   ├── sharing/
│   └── trash/
├── config/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   └── utils/
└── tests/
```

**Structure Decision**: Web application with separate frontend (React/Leaflet) and backend (Django REST). Feature is implemented in frontend/src/pages, components, hooks, and services.

## Phase 0: Outline & Research
All critical clarifications are resolved in the spec. Research tasks:
- Research browser geolocation API reliability and permission handling best practices for React/Leaflet.
- Research accessibility patterns for map markers and notifications (WCAG 2.1 AA).
- Research real-time position update strategies for web apps (polling vs. event-driven).
- Research error and permission denial notification UX for web mapping applications.

Findings will be consolidated in `research.md` with decisions, rationale, and alternatives.

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. Extract entities from feature spec → `data-model.md`:
   - DevicePosition: latitude, longitude, timestamp
   - BlueDot: position (DevicePosition), visible (bool)
   - PointCreationPanel: position (DevicePosition), open (bool)

2. No backend API changes required for this feature (frontend only). No new endpoints needed.

3. Contract tests: N/A (no new API endpoints)

4. Extract test scenarios from user stories:
   - Blue dot appears at device position if available
   - Blue dot moves in real time as position updates
   - User can recenter map on device position
   - Clicking blue dot opens point creation panel with device position
   - User is notified if position is unavailable or permission denied

5. Update agent file incrementally:
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`

**Output**: data-model.md, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
This section describes what the /tasks command will do (do not execute during /plan):

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (data model, quickstart)
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 10-15 numbered, ordered tasks in tasks.md

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
