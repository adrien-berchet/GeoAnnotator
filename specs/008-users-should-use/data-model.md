# Data Model: User Pseudonyms and Account Management

## Entities

### User (Extended)

**Purpose**: Core user authentication and profile entity with pseudonym and email privacy features

**Fields**:
- `id` (Integer, PK): Unique user identifier
- `pseudonym` (String, Unique, Max 100 chars): User-chosen display name for privacy
- `email` (EncryptedEmailField, Unique): Email address, encrypted at rest, displayed in plain text to owner
- `password` (PasswordField): Hashed password using PBKDF2
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last account modification timestamp
- `deleted_at` (DateTime, Nullable): Soft delete timestamp, NULL for active users
- `pending_email` (EncryptedEmailField, Nullable): Temporary storage for unconfirmed email changes

**Validation Rules**:
- `pseudonym`:
  - Required: Yes
  - Unique: Yes (case-insensitive via database index)
  - Length: 1-99 characters
  - Pattern: `/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/`
  - No spaces allowed
  - Error messages:
    - Empty: "Pseudonym is required."
    - Too long: "Pseudonym must be less than 100 characters."
    - Invalid chars: "Pseudonym can only contain letters, numbers, and simple special characters."
    - Spaces: "Pseudonym cannot contain spaces."
    - Duplicate: "This pseudonym is already taken. Please choose a different one."

- `email`:
  - Required: Yes
  - Unique: Yes
  - Format: Valid email address
  - Encryption: Fernet symmetric encryption
  - Display: Plain text to owner, never to other users

- `password`:
  - Required: Yes
  - Hashing: Django default (PBKDF2-SHA256)
  - Change requires: Old password verification

- `deleted_at`:
  - NULL: Active user
  - Non-NULL: Soft-deleted user, retained for 30 days
  - Cleanup: Automated task deletes records where `deleted_at < now() - 30 days`

**Relationships**:
- One-to-many with `Annotation` (user's geographic annotations)
- One-to-many with `Share` (content shared by user)
- One-to-many with `AccountLog` (audit trail of account operations)

**State Transitions**:
```
[Created] → (user registers) → [Active]
[Active] → (update pseudonym) → [Active with new pseudonym]
[Active] → (change email) → [Active with pending_email]
  → (confirm email) → [Active with new email]
  → (email expires after 30 min) → [Active with original email]
[Active] → (change password) → [Active]
[Active] → (delete account) → [Soft Deleted]
[Soft Deleted] → (30 days pass) → [Permanently Deleted]
```

**Database Schema**:
```sql
CREATE TABLE users_user (
    id SERIAL PRIMARY KEY,
    pseudonym VARCHAR(100) NOT NULL,
    email BYTEA NOT NULL,  -- Encrypted
    password VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    pending_email BYTEA NULL
);

CREATE UNIQUE INDEX users_user_pseudonym_lower_unique
ON users_user (LOWER(pseudonym));

CREATE UNIQUE INDEX users_user_email_unique
ON users_user (email) WHERE deleted_at IS NULL;

CREATE INDEX users_user_deleted_at_idx
ON users_user (deleted_at) WHERE deleted_at IS NOT NULL;
```

---

### EmailChangeConfirmation (New)

**Purpose**: Temporary token storage for email change confirmation flow

**Fields**:
- `id` (Integer, PK): Unique confirmation identifier
- `user` (ForeignKey to User): User requesting email change
- `new_email` (EncryptedEmailField): Requested new email address
- `token` (String, 128 chars): HMAC-based confirmation token
- `created_at` (DateTime): Token creation timestamp
- `expires_at` (DateTime): Token expiration timestamp (created_at + 30 minutes)
- `confirmed_at` (DateTime, Nullable): Timestamp when confirmed, NULL if pending

**Validation Rules**:
- `new_email`:
  - Must be different from current user email
  - Must not be in use by another user
  - Must be valid email format

- `token`:
  - Generated via `EmailChangeTokenGenerator`
  - Single-use (deleted after confirmation)
  - Expires after 30 minutes

**State Transitions**:
```
[Created] → (user requests email change) → [Pending]
[Pending] → (user clicks link within 30 min) → [Confirmed] → (token deleted)
[Pending] → (30 min passes) → [Expired] → (cleanup task deletes)
```

**Database Schema**:
```sql
CREATE TABLE users_emailchangeconfirmation (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    new_email BYTEA NOT NULL,
    token VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE INDEX users_emailchangeconfirmation_expires_at_idx
ON users_emailchangeconfirmation (expires_at) WHERE confirmed_at IS NULL;
```

---

### AccountLog (New)

**Purpose**: Audit trail for sensitive account operations

**Fields**:
- `id` (Integer, PK): Unique log identifier
- `user` (ForeignKey to User): User whose account was modified
- `operation` (String, Max 50 chars): Type of operation (enum)
- `ip_address` (IPAddressField, Nullable): Client IP address
- `user_agent` (String, Max 256 chars, Nullable): Client user agent
- `timestamp` (DateTime): When operation occurred
- `details` (JSONField, Nullable): Additional operation-specific data

**Operation Types** (Enum):
- `PSEUDONYM_CHANGED`: User updated pseudonym
- `EMAIL_CHANGED`: User confirmed email change
- `PASSWORD_CHANGED`: User changed password
- `ACCOUNT_DELETED`: User soft-deleted account
- `EMAIL_CHANGE_REQUESTED`: User requested email change
- `EMAIL_CHANGE_CONFIRMED`: User confirmed email change

**Validation Rules**:
- `operation`: Must be one of defined enum values
- `timestamp`: Automatically set to current time
- Logs are immutable (insert-only, no updates/deletes)

**Database Schema**:
```sql
CREATE TABLE users_accountlog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE SET NULL,
    operation VARCHAR(50) NOT NULL,
    ip_address INET NULL,
    user_agent VARCHAR(256) NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    details JSONB NULL
);

CREATE INDEX users_accountlog_user_id_idx ON users_accountlog (user_id);
CREATE INDEX users_accountlog_timestamp_idx ON users_accountlog (timestamp DESC);
CREATE INDEX users_accountlog_operation_idx ON users_accountlog (operation);
```

---

### Share (Modified)

**Purpose**: Tracks content shared between users, updated to support pseudonym display and account deletion

**Modified Fields**:
- `shared_by` (ForeignKey to User): User who shared content (displays pseudonym)
- `is_active` (Boolean): True if share is active, False if unshared (due to account deletion or manual unshare)

**Behavior Changes**:
- Display `shared_by.pseudonym` instead of `shared_by.email` in sharing lists
- When `shared_by` user is soft-deleted:
  - Set `is_active = False` immediately
  - Retain share record for 30 days
  - Permanently delete share when user is permanently deleted (CASCADE)

**Validation Rules**:
- Pseudonym updates: No validation needed (display text only changes)
- Share referential integrity: Maintained via foreign key CASCADE on permanent delete

**State Transitions**:
```
[Created] → (user shares content) → [Active]
[Active] → (user unshares) → [Inactive]
[Active] → (sharer account deleted) → [Inactive] → (30 days) → [Deleted]
```

**Database Schema** (Migration):
```sql
-- Add is_active column if not exists
ALTER TABLE sharing_share
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Index for filtering active shares
CREATE INDEX sharing_share_is_active_idx
ON sharing_share (is_active) WHERE is_active = TRUE;
```

---

## Relationships Diagram

```
User
├── 1:N → Annotation (user's content)
├── 1:N → Share (shared_by)
├── 1:N → AccountLog (audit trail)
└── 1:1 → EmailChangeConfirmation (pending email change, optional)

Share
├── N:1 → User (shared_by, displays pseudonym)
└── N:1 → Annotation (content being shared)

EmailChangeConfirmation
└── N:1 → User (requesting user)

AccountLog
└── N:1 → User (subject of log)
```

---

## Encryption Strategy

**Email Encryption**:
- Library: `django-fernet-fields`
- Algorithm: Fernet (symmetric encryption with HMAC authentication)
- Key: Stored in `settings.FERNET_KEY` environment variable
- Key rotation: Manual process (decrypt with old key, re-encrypt with new key)
- Performance: ~0.5ms overhead per encryption/decryption operation

**Implementation**:
```python
from fernet_fields import EncryptedEmailField

class User(AbstractBaseUser):
    email = EncryptedEmailField()
    pending_email = EncryptedEmailField(null=True, blank=True)
```

**Security Considerations**:
- Keys never committed to version control
- Production keys rotated quarterly
- Database backups encrypted at rest
- Application logs never contain plain text emails (except for authenticated owner viewing)

---

## Indexing Strategy

**Performance-Critical Indexes**:
1. `users_user.pseudonym` (UNIQUE, LOWER): O(log n) pseudonym uniqueness checks
2. `users_user.email` (UNIQUE): O(log n) authentication lookups
3. `users_user.deleted_at` (PARTIAL, WHERE NOT NULL): O(log n) soft-deleted user queries
4. `sharing_share.is_active` (PARTIAL, WHERE TRUE): O(log n) active share filtering
5. `users_accountlog.user_id`: O(log n) user audit trail retrieval
6. `users_accountlog.timestamp` (DESC): O(log n) recent activity queries

**Query Optimization**:
- Active users: `User.objects.filter(deleted_at__isnull=True)` uses index
- Pseudonym validation: `User.objects.filter(pseudonym__iexact=value).exists()` uses lowercase index
- Active shares: `Share.objects.filter(is_active=True)` uses partial index

---

## Migration Plan

**Migration Order**:
1. Add `pseudonym` field to User model (nullable initially for backfill)
2. Backfill pseudonyms for existing users (generate from email prefix or prompt users)
3. Add uniqueness constraint on pseudonym (after backfill complete)
4. Add `deleted_at` field to User model
5. Add `pending_email` field to User model
6. Create `EmailChangeConfirmation` model
7. Create `AccountLog` model
8. Add `is_active` field to Share model
9. Create all indexes

**Backward Compatibility**:
- Existing users without pseudonyms: Prompt for pseudonym on next login
- Email display: Gradually replace email with pseudonym across frontend
- Sharing: Update sharing queries to use `is_active=True` filter

---

## Summary

**New Models**:
- `EmailChangeConfirmation`: Temporary token storage for email changes
- `AccountLog`: Audit trail for account operations

**Modified Models**:
- `User`: Add pseudonym, deleted_at, pending_email, email encryption
- `Share`: Add is_active flag, update to display pseudonym

**Total Fields Added**: 8
**Total Indexes Added**: 6
**Total Migrations**: 9

Ready for API contract generation.
