# API Contract: Account Management

## Base URL
`/api/account/`

---

## GET /api/account/

**Description**: Retrieve current authenticated user's account information

**Authentication**: Required (JWT token)

**Request**:
```http
GET /api/account/
Authorization: Bearer {jwt_token}
```

**Response 200 OK**:
```json
{
  "id": 123,
  "pseudonym": "john_doe_2024",
  "email": "john.doe@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-11-12T14:20:00Z"
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Notes**:
- `email` is decrypted and shown in plain text to the account owner only
- Deleted users (deleted_at != NULL) return 404
- Response excludes `password`, `deleted_at`, `pending_email` fields

---

## PATCH /api/account/

**Description**: Update account pseudonym

**Authentication**: Required (JWT token)

**Request**:
```http
PATCH /api/account/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "pseudonym": "new_pseudonym_123"
}
```

**Response 200 OK**:
```json
{
  "id": 123,
  "pseudonym": "new_pseudonym_123",
  "email": "john.doe@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-11-12T14:25:00Z"
}
```

**Response 400 Bad Request** (validation error):
```json
{
  "pseudonym": [
    "This pseudonym is already taken. Please choose a different one."
  ]
}
```

**Response 400 Bad Request** (invalid format):
```json
{
  "pseudonym": [
    "Pseudonym cannot contain spaces."
  ]
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Validation Rules**:
- Length: 1-99 characters
- Pattern: `/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/`
- No spaces
- Case-insensitive uniqueness

**Side Effects**:
- Creates `AccountLog` entry with operation=PSEUDONYM_CHANGED
- Updates all sharing references display text (no link changes)

---

## POST /api/account/change-email/

**Description**: Initiate email change process (sends confirmation link)

**Authentication**: Required (JWT token)

**Request**:
```http
POST /api/account/change-email/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "new_email": "new.email@example.com"
}
```

**Response 200 OK**:
```json
{
  "detail": "Confirmation email sent to new.email@example.com. Please check your inbox.",
  "expires_at": "2024-11-12T15:00:00Z"
}
```

**Response 400 Bad Request** (email in use):
```json
{
  "new_email": [
    "This email address is already in use."
  ]
}
```

**Response 400 Bad Request** (invalid email):
```json
{
  "new_email": [
    "Enter a valid email address."
  ]
}
```

**Response 400 Bad Request** (same as current):
```json
{
  "new_email": [
    "New email must be different from current email."
  ]
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Side Effects**:
- Creates `EmailChangeConfirmation` record with token
- Sends confirmation email to `new_email` with link
- Creates `AccountLog` entry with operation=EMAIL_CHANGE_REQUESTED
- Token expires in 30 minutes

**Email Template**:
```
Subject: Confirm your email address change

Hi {pseudonym},

You requested to change your email address to {new_email}.

Please click the link below to confirm this change:
{confirmation_link}

This link will expire in 30 minutes.

If you didn't request this change, please ignore this email.
```

---

## POST /api/account/confirm-email/

**Description**: Confirm email change with token from email link

**Authentication**: Required (JWT token)

**Request**:
```http
POST /api/account/confirm-email/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "token": "abc123def456...",
  "user_id": 123
}
```

**Response 200 OK**:
```json
{
  "detail": "Email address updated successfully.",
  "new_email": "new.email@example.com"
}
```

**Response 400 Bad Request** (invalid token):
```json
{
  "detail": "Invalid or expired confirmation token."
}
```

**Response 400 Bad Request** (expired):
```json
{
  "detail": "Confirmation link has expired. Please request a new one."
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Response 403 Forbidden** (wrong user):
```json
{
  "detail": "You do not have permission to confirm this email change."
}
```

**Side Effects**:
- Updates `User.email` to new email
- Deletes `EmailChangeConfirmation` record
- Creates `AccountLog` entry with operation=EMAIL_CHANGE_CONFIRMED

---

## POST /api/account/change-password/

**Description**: Change user password (requires old password verification)

**Authentication**: Required (JWT token)

**Request**:
```http
POST /api/account/change-password/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "old_password": "current_password_123",
  "new_password": "new_secure_password_456"
}
```

**Response 200 OK**:
```json
{
  "detail": "Password changed successfully."
}
```

**Response 400 Bad Request** (incorrect old password):
```json
{
  "old_password": [
    "Current password is incorrect."
  ]
}
```

**Response 400 Bad Request** (weak new password):
```json
{
  "new_password": [
    "This password is too common.",
    "This password is too short. It must contain at least 8 characters."
  ]
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Side Effects**:
- Updates `User.password` with hashed new password
- Creates `AccountLog` entry with operation=PASSWORD_CHANGED
- Invalidates all existing JWT tokens (user must re-login)

**Validation Rules**:
- Old password must match current password
- New password must meet Django password validation requirements:
  - Minimum 8 characters
  - Not too common
  - Not too similar to user attributes
  - Not entirely numeric

---

## DELETE /api/account/

**Description**: Soft delete user account (sends confirmation email)

**Authentication**: Required (JWT token)

**Request**:
```http
DELETE /api/account/
Authorization: Bearer {jwt_token}
```

**Response 200 OK**:
```json
{
  "detail": "Account deletion confirmation sent. Please check your email.",
  "warning": "Your account and all associated data will be permanently deleted in 30 days."
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Side Effects**:
- Sends deletion confirmation email with warning
- Does NOT set `deleted_at` until email confirmation
- Creates `AccountLog` entry with operation=ACCOUNT_DELETE_REQUESTED

**Email Template**:
```
Subject: Confirm account deletion

Hi {pseudonym},

You requested to delete your account.

⚠️ WARNING: This action cannot be undone. All your annotations and shared content will be permanently deleted in 30 days.

Please click the link below to confirm account deletion:
{confirmation_link}

If you didn't request this, please ignore this email and your account will remain active.
```

---

## POST /api/account/confirm-delete/

**Description**: Confirm account deletion with token from email link

**Authentication**: Required (JWT token)

**Request**:
```http
POST /api/account/confirm-delete/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "token": "xyz789abc123...",
  "user_id": 123
}
```

**Response 200 OK**:
```json
{
  "detail": "Account deleted successfully. Your data will be permanently removed in 30 days.",
  "deleted_at": "2024-11-12T14:30:00Z",
  "permanent_deletion_date": "2024-12-12T14:30:00Z"
}
```

**Response 400 Bad Request** (invalid token):
```json
{
  "detail": "Invalid or expired deletion confirmation token."
}
```

**Response 401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Response 403 Forbidden** (wrong user):
```json
{
  "detail": "You do not have permission to confirm this deletion."
}
```

**Side Effects**:
- Sets `User.deleted_at` to current timestamp
- Unshares all user's content (sets `Share.is_active = False`)
- Creates `AccountLog` entry with operation=ACCOUNT_DELETED
- Invalidates all JWT tokens for this user
- Schedules permanent deletion in 30 days via cleanup task

---

## Validation Endpoint

## POST /api/account/validate-pseudonym/

**Description**: Validate pseudonym without saving (for frontend inline validation)

**Authentication**: Optional (can be used during registration)

**Request**:
```http
POST /api/account/validate-pseudonym/
Content-Type: application/json

{
  "pseudonym": "test_pseudonym_123"
}
```

**Response 200 OK** (valid and available):
```json
{
  "valid": true,
  "available": true
}
```

**Response 200 OK** (valid but taken):
```json
{
  "valid": true,
  "available": false,
  "error": "This pseudonym is already taken. Please choose a different one."
}
```

**Response 200 OK** (invalid format):
```json
{
  "valid": false,
  "available": null,
  "error": "Pseudonym cannot contain spaces."
}
```

**Notes**:
- Used for frontend debounced validation as user types
- Case-insensitive uniqueness check
- Does not create or modify any records

---

## Error Response Format

All error responses follow Django REST Framework standard format:

```json
{
  "field_name": ["Error message 1", "Error message 2"],
  "another_field": ["Error message"]
}
```

Or for non-field errors:

```json
{
  "detail": "Error message"
}
```

---

## Rate Limiting

- Account operations: 10 requests per minute per user
- Email sending (change-email, delete): 3 requests per hour per user
- Validation endpoint: 30 requests per minute per IP

**Rate Limit Response 429**:
```json
{
  "detail": "Request was throttled. Expected available in 45 seconds."
}
```

---

## Summary

**Endpoints**: 7
- GET /api/account/ (retrieve)
- PATCH /api/account/ (update pseudonym)
- POST /api/account/change-email/ (initiate)
- POST /api/account/confirm-email/ (confirm)
- POST /api/account/change-password/ (update)
- DELETE /api/account/ (initiate deletion)
- POST /api/account/confirm-delete/ (confirm deletion)
- POST /api/account/validate-pseudonym/ (validation helper)

**Authentication**: JWT bearer token required for all except validation endpoint

**Side Effects Tracking**: All operations logged to `AccountLog` for audit trail
