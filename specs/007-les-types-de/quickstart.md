# Quickstart: Multilingual Point Type Names

## Goal
Enable multilingual display and editing of point type names for both base and custom types, with fallback logic and translation management.

## Steps
1. User logs in and sets language preference.
2. User views list of point types:
   - Names are shown in user's language if available.
   - If not, fallback to English, then to creation language for custom types.
3. User creates a custom point type:
   - Enters name (stored with user's language).
   - Optionally adds translations in other languages.
4. User edits a custom point type:
   - Adds or removes translations (cannot remove last one).
5. User verifies fallback logic by switching language preference and viewing point types.

## Validation
- All acceptance scenarios from the spec are covered.
- Edge cases (missing translation, duplicate, last translation removal) are handled.

---
