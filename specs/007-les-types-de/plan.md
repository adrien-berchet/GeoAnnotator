

# Implementation Plan: Multilingual Point Type Names

**Branch**: `007-les-types-de` | **Date**: 2025-10-20 | **Spec**: /specs/007-les-types-de/spec.md
**Input**: Feature specification from `/specs/007-les-types-de/spec.md`

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

## Summary
Enable multilingual display and editing of point type names for both base and custom types, with fallback logic and translation management. The technical approach is to store all names as a map of language code to string, with a creation language for custom types, and to expose REST endpoints for CRUD and translation management.

## Technical Context
**Language/Version**: TypeScript 5.9.3 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 19.1.1, Vite 7.1.7, Django REST Framework, PostgreSQL
**Storage**: PostgreSQL
**Testing**: pytest, vitest
**Target Platform**: Web (Linux server, modern browsers)
**Project Type**: web (frontend + backend)
**Performance Goals**: API <200ms p95 reads, <500ms p95 writes
**Constraints**: Bundle <300KB, memory <512MB, WCAG 2.1 AA, English-first UI
**Scale/Scope**: 10k users, 100+ point types

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
specs/007-les-types-de/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Web application (frontend + backend) with Django REST Framework and React.

## Phase 0: Outline & Research
- All clarifications resolved; see research.md for fallback logic and language storage decisions.

## Phase 1: Design & Contracts
- See data-model.md for entities and validation rules.
- See contracts/ for OpenAPI and contract tests.
- See quickstart.md for user and test scenarios.
- Agent context updated via update-agent-context.sh copilot.

## Phase 2: Task Planning Approach
- /tasks command will generate tasks from contracts, data model, and quickstart.
- TDD order: contract tests, then models/services, then UI.
- Parallelize independent contract/entity tasks.

## Complexity Tracking
No deviations from constitution expected.

## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Code Quality Standards**:
- [ ] Code will adhere to linting and type checking standards
- [ ] All code will be documented in English with clear API descriptions
- [ ] Complexity limits will be respected (functions <50 lines, complexity <10)

**Testing Requirements**:
- [ ] TDD approach planned (tests before implementation)
- [ ] Coverage targets defined (≥80% general, ≥95% critical paths)
- [ ] Unit, integration, and E2E test types identified

**User Experience Consistency**:
- [ ] All UI/UX elements designed in English (US)
- [ ] WCAG 2.1 Level AA accessibility considered
- [ ] Responsive design planned (320px-2560px viewports)
- [ ] Error messages planned with clear, actionable English text

**Performance Requirements**:
- [ ] API response time targets defined (<200ms p95 reads, <500ms p95 writes)
- [ ] Resource efficiency targets set (bundle size <300KB, memory <512MB)
- [ ] Performance monitoring and load testing planned

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

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
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
