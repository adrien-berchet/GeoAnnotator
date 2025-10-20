# Research: Multilingual Point Type Names

## Unknowns and Research Tasks
- No outstanding NEEDS CLARIFICATION remain in the spec.
- All fallback and language storage rules are clarified.

## Decisions
- Fallback order for point type names: user language → English → creation language (for custom types).
- All language codes must be stored for each translation and for the creation language of custom types.

## Rationale
- Ensures users always see a name, even if not in their preferred language.
- Supports internationalization and user flexibility.

## Alternatives Considered
- Fallback to random available translation: rejected for predictability and user experience.
- Forcing English for all types: rejected to allow user-created types in any language.

---

No further research tasks required at this stage.
