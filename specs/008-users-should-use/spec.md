# Feature Specification: User Pseudonyms and Account Management

**Feature Branch**: `008-users-should-use`
**Created**: 2025-11-12
**Status**: Draft
**Input**: User description: "Users should use a pseudo and their email addresses should be ciphered to avoid private data leaks. This pseudo is used for sharings so that other users can not see email addresses. The pseudo is displayed on the menu bar instead of the email address. Also, the user profile page should be renamed 'account'. This page should allow to manage the pseudo, the email address, the password and to delete the account (with a warning and an email confirmation). When a user updates its pseudo, only the text is changed but all links to it remain unchanged (like sharing for example)."

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature description provided
2. Extract key concepts from description
   → Actors: authenticated users, sharing recipients
   → Actions: create/update pseudo, manage account, share content, delete account
   → Data: pseudonym, email (encrypted), password, account settings
   → Constraints: privacy protection, pseudo uniqueness, sharing link stability
3. For each unclear aspect:
   → All clarifications resolved (see Clarifications section)
4. Fill User Scenarios & Testing section
   → Primary flow identified
5. Generate Functional Requirements
   → Requirements marked where ambiguous
6. Identify Key Entities (if data involved)
   → User account, pseudonym, sharing references
7. Run Review Checklist
   → All checks passed
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-11-12

- Q: Email change process - how is the new email address validated? → A: Confirmation link sent to new address, valid for 30 minutes. New address used only after validation.
- Q: Account deletion - what happens to user's annotations and shared content? → A: Shared content immediately unshared, actual database deletion after 30 days.
- Q: Pseudonym uniqueness requirement across all users? → A: Yes, must be unique across all users.
- Q: Pseudonym validation rules - length, allowed characters? → A: Length < 100 characters, no spaces, simple special characters and numbers allowed. Frontend warning displayed if invalid.
- Q: Password change - require old password for verification? → A: Yes, old password required for verification.
- Q: Email encryption visibility - can user see their own email in plain text? → A: Yes, user sees plain text. Encryption only in database.

---

## User Scenarios & Testing

### Primary User Story
An authenticated user wants to protect their email address privacy while sharing geographic annotations with others. They create a unique pseudonym that will be displayed throughout the application instead of their email address. When sharing content, other users see only the pseudonym, not the email address. The user can manage all account settings including the pseudonym, email, and password from a centralized account management page, and can delete their account if needed.

### Acceptance Scenarios

#### Pseudonym Creation and Display
1. **Given** a new user account without a pseudonym, **When** the user accesses the account page, **Then** the system prompts them to create a pseudonym
2. **Given** a user has set a pseudonym, **When** the user views any part of the application, **Then** the pseudonym is displayed instead of the email address in the menu bar
3. **Given** a user has shared content with others, **When** recipients view the shared content, **Then** they see the sharer's pseudonym, not their email address

#### Account Management
4. **Given** a user is on the account page, **When** they view their settings, **Then** they can see and modify their pseudonym, email address (in plain text), and password
5. **Given** a user updates their pseudonym, **When** the change is saved, **Then** the new pseudonym appears everywhere in the UI but all existing sharing links remain functional
6. **Given** a user changes their email address, **When** they submit the new address, **Then** the system sends a confirmation link to the new address (valid for 30 minutes) and the email is only updated after confirmation
7. **Given** a user changes their password, **When** they submit the form, **Then** the system requires the old password for verification before allowing the change

#### Account Deletion
8. **Given** a user initiates account deletion, **When** they confirm the action, **Then** the system displays a warning message and sends a confirmation email
9. **Given** a user receives the deletion confirmation email, **When** they click the confirmation link within the valid timeframe, **Then** their account is permanently deleted
10. **Given** a user has deleted their account, **When** other users access previously shared content, **Then** the content is immediately unshared and will be deleted from the database after 30 days

### Edge Cases

#### Pseudonym Constraints
- What happens when a user tries to create a pseudonym that already exists? System rejects it and displays an error message requiring a unique pseudonym.
- What happens when a user enters invalid characters or exceeds length limits in their pseudonym? System displays a frontend warning indicating validation rules (< 100 characters, no spaces, simple special characters and numbers allowed).
- What happens when a user tries to create an empty or whitespace-only pseudonym? System rejects it and requires a valid pseudonym.

#### Email and Password Management
- What happens when a user changes their email to an address already in use by another account? System rejects the change and displays an error message.
- What happens when a user enters an incorrect current password while trying to change it? System rejects the password change and displays an error message.
- What happens when the email change confirmation link is not clicked within 30 minutes? The link expires and the email address remains unchanged.
- What happens when the account deletion confirmation email is not received or expires? The account deletion is not completed and the account remains active.

#### Data Privacy
- How is email encryption handled when users need to receive system emails (password reset, deletion confirmation)?
- What happens when administrators need to contact users for support or security issues?

---

## Requirements

### Functional Requirements

#### Pseudonym Management
- **FR-001**: System MUST allow users to create and set a unique pseudonym for their account
- **FR-002**: System MUST display the user's pseudonym instead of their email address in the menu bar
- **FR-003**: System MUST display the pseudonym of content sharers instead of their email addresses to content recipients
- **FR-004**: System MUST validate pseudonyms with the following rules: length less than 100 characters, no spaces allowed, simple special characters and numbers allowed
- **FR-005**: System MUST enforce pseudonym uniqueness across all users
- **FR-006**: System MUST display a frontend warning when a pseudonym does not meet validation rules
- **FR-007**: System MUST allow users to update their pseudonym at any time
- **FR-008**: System MUST preserve all existing sharing links and references when a pseudonym is updated (only display text changes)

#### Email Privacy
- **FR-009**: System MUST encrypt user email addresses in the database to prevent private data leaks
- **FR-010**: System MUST never display user email addresses to other users in any context
- **FR-011**: System MUST allow users to view their own email address in plain text in the Account page
- **FR-012**: System MUST send a confirmation link to the new email address when a user changes their email
- **FR-013**: Email change confirmation link MUST expire after 30 minutes
- **FR-014**: System MUST update the email address only after the user clicks the confirmation link

#### Account Management Page
- **FR-015**: System MUST rename the user profile page to "Account"
- **FR-016**: Account page MUST provide interface to view and update pseudonym
- **FR-017**: Account page MUST provide interface to view and update email address (displayed in plain text)
- **FR-018**: Account page MUST provide interface to change password
- **FR-019**: Account page MUST provide interface to delete the account
- **FR-020**: Password change MUST require verification of the old password before allowing the change
- **FR-021**: Email address changes MUST validate uniqueness across all user accounts

#### Account Deletion
- **FR-022**: System MUST display a warning message when user initiates account deletion
- **FR-023**: System MUST send a confirmation email to the user's registered email address before deleting the account
- **FR-024**: System MUST require the user to click a confirmation link in the email to complete account deletion
- **FR-025**: System MUST immediately unshare all shared content when account deletion is confirmed
- **FR-026**: System MUST retain user's annotations and shared content for 30 days after account deletion before permanent database deletion
- **FR-027**: System MUST permanently delete the user account data from the database 30 days after deletion confirmation

#### Security and Accessibility
- **FR-028**: System MUST ensure all account management operations are accessible only to authenticated users managing their own account
- **FR-029**: System MUST log all sensitive account operations (email change, password change, account deletion)
- **FR-030**: Account management page MUST be accessible and meet WCAG 2.1 Level AA standards
- **FR-031**: Account management page MUST be responsive across all device breakpoints (320px-2560px)

### Key Entities

- **User Account**: Represents an authenticated user in the system with essential credentials and preferences
  - Has a unique pseudonym (display name for privacy, must be unique across all users)
  - Has an encrypted email address in database (displayed in plain text to owner, used for authentication and critical communications)
  - Has authentication credentials (password)
  - Associated with annotations and shared content
  - Soft-deleted with 30-day retention period before permanent deletion

- **Pseudonym**: A user-chosen display name that protects email privacy
  - Must be unique across all users
  - Can be updated without breaking existing references
  - Used in all sharing and collaboration contexts
  - Validation rules: length < 100 characters, no spaces, simple special characters and numbers allowed
  - Frontend warning displayed when validation fails

- **Account Settings**: User-manageable configuration accessible from Account page
  - Includes pseudonym, email address (plain text view), password
  - Provides account deletion capability
  - All operations require authentication
  - Email changes require confirmation via link (30-minute expiry)
  - Password changes require old password verification

- **Sharing Reference**: Link or reference to content shared with other users
  - Associates with pseudonym for display
  - Remains stable when pseudonym text is updated
  - Immediately unshared when account is deleted
  - Content retained for 30 days before permanent database deletion

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
- [x] All clarifications resolved

---
