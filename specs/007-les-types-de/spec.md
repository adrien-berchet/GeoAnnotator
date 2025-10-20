# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)

- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **English Language**: All specifications MUST be written in English (US)
5. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale (response times, resource limits)
   - Error handling behaviors and user-facing error messages
   - Integration requirements
   - Security/compliance needs
   - Responsive design breakpoints (320px-2560px)

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
[Describe the main user journey in plain language]

### Acceptance Scenarios
1. **Given** [initial state], **When** [action], **Then** [expected outcome]
### Edge Cases
- What happens when [boundary condition]?
- How does system handle [error scenario]?

- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
*Example of marking unclear requirements:*
- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
### Key Entities *(include if feature involves data)*
- **[Entity 2]**: [What it represents, relationships to other entities]

---

## Review & Acceptance Checklist
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] Success criteria are measurable
- [ ] Dependencies and assumptions identified

---

- [ ] Requirements generated
**Feature Specification: Multilingual Point Type Names**

**Feature Branch**: `007-les-types-de`
**Created**: 2025-10-20
**Status**: Draft
**Input**: User description: "Les types de point de base sont des types génériques visibles par tous les utilisateurs, il faut donc que leurs noms s'adaptent à la langue de l'utilisateur. Il faut donc ajouter un mécanisme pour permettre le stockage des noms en plusieurs langue et le choix pour l'affiissage se fait en fonction de la langue de l'utilisateur. Quant aux types personnalisés, l'utilisateur doit également avoir la possibilité d'ajouter des noms dans plusieurs langues s'il le souhaite. Par défaut, le nom entré par l'utilisateur est associé à la langue de l'utilisateur mais un bouton lui permet d'ajouter les noms dans les autres langues de son choix."

## Execution Flow (main)
```
1. Parse user description from Input
    → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
    → Identify: actors, actions, data, constraints
3. For each unclear aspect:
    → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
    → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
    → Each requirement must be testable
    → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
    → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
    → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A user views or creates point types (base or custom). The names of base point types are displayed in the user's preferred language. When creating or editing a custom point type, the user can provide names in multiple languages. By default, the entered name is saved in the user's language, but the user can add translations for other languages via an interface control.

### Acceptance Scenarios
1. **Given** a user with a set language preference, **When** viewing base point types, **Then** the names are displayed in the user's language if available, otherwise a fallback is used.
2. **Given** a user creating a custom point type, **When** entering a name, **Then** the name is stored with the user's language as default.
3. **Given** a user editing a custom point type, **When** adding a translation, **Then** the new language name is stored and selectable for display.
4. **Given** a user viewing a point type with no translation in their language, **When** accessing the list, **Then** a fallback language (e.g., English) is shown.

### Edge Cases
- What happens when a translation is missing for the user's language?
- How does the system handle duplicate language entries for a point type?
- What if a user tries to remove the only available translation?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST store point type names in multiple languages for both base and custom types.
- **FR-002**: System MUST display point type names in the user's preferred language if available.
- **FR-003**: System MUST allow users to add translations for custom point type names in additional languages.
- **FR-004**: System MUST associate the initially entered name for a custom type with the user's current language.
- **FR-005**: System MUST provide a UI control to add or edit translations for custom point type names.
- **FR-006**: System MUST provide a fallback mechanism when a translation is missing for the user's language.
- **FR-007**: System MUST prevent duplicate language entries for a single point type name.
- **FR-008**: System MUST prevent removal of the last remaining translation for a point type.
- **FR-009**: System MUST ensure all users see base point type names in their selected language if available.
- **FR-010**: If no translation is available for the current user language, the system MUST fallback to English. For custom point types, if English is not available, the system MUST fallback to the language in which the custom type was created (which must be stored; for base types, this is always English).

### Key Entities
- **PointType**: Represents a type of point (base or custom). Attributes: id, type (base/custom), names (map of language code → name), owner (for custom types), visibility.
- **User**: Has a language preference used for display.

## Clarifications
### Session 2025-10-20
- Q: What is the fallback language order if no translation is available? → A: If no translation is available for the current user language, fallback to English. For custom point types, if English is not available, fallback to the language in which the custom type was created (which must be stored; for base types, this is always English).

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---
- [ ] Review checklist passed

---
