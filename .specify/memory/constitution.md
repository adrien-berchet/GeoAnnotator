<!--
  Sync Impact Report
  ==================
  Version Change: 1.0.1 → 1.0.2 (Compliance audit and date synchronization)

  Audit Summary (2025-11-27):
  - Constitution reviewed for alignment with current project state
  - All principles validated against GeoAnnotator codebase
  - No breaking changes or new principles required

  Verified Compliance:
  - ✅ Code Quality: ESLint, TypeScript, Ruff, Black configured
  - ✅ Testing: pytest (backend), vitest (frontend) with coverage
  - ✅ UX Consistency: English-first, responsive design, accessibility
  - ✅ Performance: API monitoring, Sentry integration active

  Templates Status:
  - ✅ .specify/templates/plan-template.md (aligned with constitution)
  - ✅ .specify/templates/spec-template.md (aligned with constitution)
  - ✅ .specify/templates/tasks-template.md (aligned with constitution)
  - ✅ .specify/templates/agent-file-template.md (aligned with constitution)
  - ✅ .specify/templates/checklist-template.md (aligned with constitution)

  Follow-up TODOs:
  - None (audit complete, all items verified)

  Previous Version History:
  - 1.0.0 → 1.0.1: Clarification of code documentation language requirements
-->

# GeoAnnotator Constitution

## Core Principles

### I. Code Quality Standards

All code MUST adhere to industry-standard quality practices:
- **Static Analysis**: All code MUST pass linting and type checking before commit. No exceptions.
- **Code Review**: Every change MUST be reviewed by at least one other developer. Self-merges are prohibited.
- **Documentation**: All public APIs, components, and modules MUST include English-language documentation describing purpose, parameters, return values, and usage examples.
- **Naming Conventions**: Use clear, descriptive, English names. Abbreviations are permitted only for widely-recognized terms (e.g., HTTP, API, URL).
- **Complexity Limits**: Functions exceeding 50 lines or cyclomatic complexity >10 MUST be refactored or explicitly justified in code comments.

**Rationale**: Consistent quality standards ensure maintainability, reduce technical debt, and facilitate onboarding of new contributors.

### II. Testing Requirements

Testing is non-negotiable and MUST follow Test-Driven Development (TDD):
- **Test-First Development**: Tests MUST be written before implementation code. Red-Green-Refactor cycle strictly enforced.
- **Coverage Minimum**: All features MUST achieve ≥80% code coverage. Critical paths (authentication, data persistence, payments) require ≥95% coverage.
- **Test Types Required**:
  - **Unit Tests**: All business logic, utilities, and data transformations
  - **Integration Tests**: API contracts, database operations, external service interactions
  - **End-to-End Tests**: Critical user journeys and happy paths
- **Test Quality**: Tests MUST be deterministic, independent, and fast (<100ms per unit test). Flaky tests MUST be fixed immediately or disabled with a tracking issue.
- **Continuous Integration**: All tests MUST pass in CI before merge. Breaking the build blocks all deployments.

**Rationale**: TDD prevents regressions, documents expected behavior, and enables confident refactoring.

### III. User Experience Consistency

All user-facing features MUST deliver a consistent, accessible experience:
- **English-First Design**: All UI text, messages, labels, and documentation MUST be in English (US). Future internationalization is acceptable but English is the primary language.
- **Accessibility Standards**: MUST comply with WCAG 2.1 Level AA guidelines (keyboard navigation, screen reader support, color contrast ratios ≥4.5:1).
- **Responsive Design**: Interfaces MUST function correctly on viewport widths from 320px (mobile) to 2560px (desktop).
- **Error Handling**: User-facing errors MUST provide clear, actionable English messages. No technical stack traces or cryptic codes shown to end users.
- **Consistent Patterns**: Reuse established UI components, interaction patterns, and design tokens. Custom components require design review approval.
- **Loading & Feedback**: Operations exceeding 200ms MUST show progress indicators. Users MUST receive confirmation for all destructive actions.

**Rationale**: Consistency reduces cognitive load, improves accessibility, and builds user trust.

### IV. Performance Requirements

Performance is a feature with measurable targets:
- **Response Times**:
  - API endpoints MUST respond within 200ms (p95) for read operations
  - API endpoints MUST respond within 500ms (p95) for write operations
  - Page loads MUST complete initial render within 1.5s (p95) on 3G networks
- **Resource Efficiency**:
  - Client-side bundles MUST remain under 300KB (gzipped) for initial load
  - Memory usage MUST not exceed 512MB for typical user sessions
  - Database queries MUST be optimized (no N+1 queries, indexes on foreign keys)
- **Scalability**: Features MUST support ≥1000 concurrent users without degradation
- **Monitoring**: All performance-critical paths MUST be instrumented with metrics (response time, throughput, error rates)
- **Performance Testing**: Load tests MUST validate targets before production deployment

**Rationale**: Poor performance degrades UX, increases infrastructure costs, and limits adoption.

## Language Requirements

**Project Language**: English (US)

All project artifacts MUST be in English:
- **Source code**:
  - Variable names, function names, class names, constants
  - Inline comments (single-line `//` or `#`, multi-line `/* */` or `"""`)
  - Docstrings and documentation strings (Python docstrings, JSDoc, Javadoc, etc.)
  - Code annotations and decorators descriptions
  - TODO, FIXME, NOTE, and other code markers
  - Type hints and type annotations
- **Tests**:
  - Test function/method names
  - Test descriptions and assertion messages
  - Test fixture names and mock data labels
- **User interface**: Labels, messages, help text, placeholders
- **Documentation**: API docs, endpoints, parameters, responses, README files
- **Project management**: Commit messages, PR descriptions, issue reports, specs, plans

**Exceptions**:
- Translatable content may be stored in internationalization (i18n) resource files
- User-generated content (e.g., annotations, comments) may be in any language
- External dependencies or libraries may use their native languages
- Domain-specific terminology may retain original language if universally recognized (e.g., "locale", "résumé" in HR context)

**Rationale**: English is the lingua franca of software development, ensuring broad accessibility to contributors and users globally. Consistent language in code and documentation reduces cognitive overhead and facilitates collaboration.

## Development Workflow

**Workflow Principles**:
1. **Feature Branching**: All work MUST occur on feature branches named `###-feature-description` (e.g., `001-user-authentication`)
2. **Specification First**: Features MUST begin with a written spec (`spec.md`) defining requirements before implementation
3. **Planning Before Coding**: Implementation plans (`plan.md`) MUST define architecture, dependencies, and task breakdown
4. **Task Tracking**: Tasks (`tasks.md`) MUST be created from plans and marked complete as work progresses
5. **Incremental Commits**: Commits MUST be small, focused, and include descriptive messages following Conventional Commits format
6. **Review Gates**: No merge to main without passing tests, code review approval, and constitution compliance verification
7. **Documentation Updates**: User-facing changes MUST include corresponding documentation updates in the same PR

**Constitution Compliance**:
- All reviews MUST verify adherence to these principles
- Violations require explicit justification or refactoring
- Complexity that cannot be simplified MUST be documented in `Complexity Tracking` sections of plans

## Governance

**Authority**: This constitution supersedes all other development practices, guidelines, or conventions.

**Amendment Procedure**:
1. Proposed amendments MUST be documented in a pull request
2. Amendments require approval from project maintainers
3. Breaking changes (MAJOR version bumps) require migration plan and deprecation notice
4. Minor additions (MINOR version bumps) require documentation of new requirements
5. Clarifications (PATCH version bumps) may be merged with single maintainer approval

**Versioning**:
- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Backward-incompatible governance changes or principle redefinitions
- MINOR: New principles or materially expanded guidance
- PATCH: Clarifications, wording improvements, typo fixes

**Compliance Review**:
- Constitution compliance MUST be verified during code review
- Automated linting and testing gates enforce testable principles
- Quarterly audits review adherence and identify improvement opportunities

**Runtime Guidance**: For AI-assisted development, agent-specific guidance files (e.g., `CLAUDE.md`, `.github/copilot-instructions.md`) supplement this constitution but never override it.

**Version**: 1.0.2 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-11-27
