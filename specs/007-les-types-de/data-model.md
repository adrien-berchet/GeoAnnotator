# Data Model: Multilingual Point Type Names

## Entities

### PointType
- id: UUID
- type: enum (base, custom)
- names: map<language_code, string>
- creation_language: string (ISO 639-1 code)
- owner: User (nullable, only for custom types)
- visibility: enum (public, private)

### User
- id: UUID
- language_preference: string (ISO 639-1 code)

## Relationships
- PointType.owner → User.id (nullable)

## Validation Rules
- At least one name (in any language) must exist for each PointType
- No duplicate language codes in names
- For base types, creation_language is always 'en'
- For custom types, creation_language is the language of the user at creation

## State Transitions
- Custom PointType: can add/remove translations (except last remaining)
- Base PointType: translations managed centrally

---
