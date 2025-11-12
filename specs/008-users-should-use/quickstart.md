# Quickstart: User Pseudonyms and Account Management

## Prerequisites

- Backend server running on `http://localhost:8000`
- Frontend development server running on `http://localhost:5173`
- PostgreSQL database initialized with migrations
- Test user account created (email: `test@example.com`, password: `testpass123`)
- Email backend configured (console or SMTP for testing)

## Environment Setup

```bash
# Backend
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser  # If not exists

# Frontend
cd frontend
npm install
npm run dev

# Both servers must be running
```

---

## Test Scenario 1: Pseudonym Creation

**Objective**: Verify new user can create a unique pseudonym

### Steps:

1. **Login as test user**
   ```bash
   # Navigate to http://localhost:5173/login
   # Enter: test@example.com / testpass123
   ```

2. **Access Account page**
   ```bash
   # Click user menu in navigation bar
   # Select "Account" (formerly "Profile")
   # Verify page title: "Account Settings"
   ```

3. **Set pseudonym**
   ```bash
   # In Pseudonym field, enter: "test_user_2024"
   # Click "Save"
   ```

4. **Verify pseudonym display**
   ```bash
   # Check navigation bar shows "test_user_2024" instead of email
   # Check Account page shows pseudonym in read-only display
   ```

### Expected Results:
- ✅ Menu bar displays pseudonym: "test_user_2024"
- ✅ Account page shows: "Pseudonym: test_user_2024"
- ✅ Email address NOT visible in menu bar
- ✅ Success message: "Pseudonym updated successfully"

### API Verification:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/account/

# Response should include:
# {
#   "pseudonym": "test_user_2024",
#   "email": "test@example.com"  # Plain text for owner
# }
```

---

## Test Scenario 2: Pseudonym Validation

**Objective**: Verify pseudonym validation rules are enforced

### Steps:

1. **Test invalid characters (spaces)**
   ```bash
   # In Pseudonym field, enter: "test user 2024"
   # Observe inline validation warning
   ```

2. **Test length limit**
   ```bash
   # Enter 100+ character pseudonym
   # Observe validation error
   ```

3. **Test duplicate pseudonym**
   ```bash
   # Create second user with pseudonym "duplicate_test"
   # Try to set first user's pseudonym to "duplicate_test"
   # Observe uniqueness error
   ```

4. **Test valid special characters**
   ```bash
   # Enter: "user_2024!@#"
   # Should save successfully
   ```

### Expected Results:
- ✅ Spaces error: "Pseudonym cannot contain spaces."
- ✅ Length error: "Pseudonym must be less than 100 characters."
- ✅ Duplicate error: "This pseudonym is already taken. Please choose a different one."
- ✅ Special chars allowed: Success

### API Verification:
```bash
# Test validation endpoint
curl -X POST http://localhost:8000/api/account/validate-pseudonym/ \
  -H "Content-Type: application/json" \
  -d '{"pseudonym": "test user"}'

# Response:
# {
#   "valid": false,
#   "available": null,
#   "error": "Pseudonym cannot contain spaces."
# }
```

---

## Test Scenario 3: Email Change with Confirmation

**Objective**: Verify email change requires confirmation link

### Steps:

1. **Initiate email change**
   ```bash
   # On Account page, click "Change Email"
   # Enter new email: "newemail@example.com"
   # Click "Send Confirmation"
   ```

2. **Check email sent**
   ```bash
   # Check console output or email inbox
   # Verify confirmation email received
   # Verify email contains: "Confirm your email address change"
   ```

3. **Click confirmation link**
   ```bash
   # Click link in email (format: /account/confirm-email?token=...&user=123)
   # Should redirect to Account page with success message
   ```

4. **Verify email updated**
   ```bash
   # Check Account page shows new email
   # Login with new email works
   # Old email no longer valid for login
   ```

### Expected Results:
- ✅ Confirmation email sent to new address
- ✅ Email contains confirmation link with token
- ✅ Link expires in 30 minutes
- ✅ After confirmation: Account shows new email
- ✅ Success message: "Email address updated successfully"

### API Verification:
```bash
# Initiate change
curl -X POST http://localhost:8000/api/account/change-email/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_email": "newemail@example.com"}'

# Response:
# {
#   "detail": "Confirmation email sent to newemail@example.com. Please check your inbox.",
#   "expires_at": "2024-11-12T15:00:00Z"
# }

# Confirm change (use token from email)
curl -X POST http://localhost:8000/api/account/confirm-email/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123...", "user_id": 123}'

# Response:
# {
#   "detail": "Email address updated successfully.",
#   "new_email": "newemail@example.com"
# }
```

---

## Test Scenario 4: Password Change with Verification

**Objective**: Verify password change requires old password

### Steps:

1. **Access password change form**
   ```bash
   # On Account page, click "Change Password"
   # Form shows: "Current Password" and "New Password" fields
   ```

2. **Test incorrect old password**
   ```bash
   # Enter wrong current password
   # Enter new password
   # Click "Change Password"
   # Observe error
   ```

3. **Test correct password change**
   ```bash
   # Enter correct current password: "testpass123"
   # Enter new password: "newsecurepass456"
   # Click "Change Password"
   ```

4. **Verify new password works**
   ```bash
   # Logout
   # Login with new password
   # Should succeed
   ```

### Expected Results:
- ✅ Incorrect old password error: "Current password is incorrect."
- ✅ Weak password validation: "This password is too common."
- ✅ Success message: "Password changed successfully"
- ✅ Old password no longer works for login
- ✅ New password works for login

### API Verification:
```bash
curl -X POST http://localhost:8000/api/account/change-password/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "testpass123",
    "new_password": "newsecurepass456"
  }'

# Response:
# {
#   "detail": "Password changed successfully."
# }
```

---

## Test Scenario 5: Account Deletion with Soft Delete

**Objective**: Verify account deletion follows 30-day retention policy

### Steps:

1. **Initiate account deletion**
   ```bash
   # On Account page, scroll to "Delete Account" section
   # Click "Delete My Account" button
   # Observe warning dialog
   ```

2. **Confirm deletion intent**
   ```bash
   # Warning shows: "This action cannot be undone. Your data will be permanently deleted in 30 days."
   # Click "Send Confirmation Email"
   ```

3. **Check deletion confirmation email**
   ```bash
   # Check email inbox
   # Verify subject: "Confirm account deletion"
   # Verify warning message in email body
   ```

4. **Click deletion confirmation link**
   ```bash
   # Click link in email
   # Should show: "Account deleted successfully. Your data will be permanently removed in 30 days."
   ```

5. **Verify account soft-deleted**
   ```bash
   # Try to login - should fail
   # Check database: deleted_at timestamp set
   # Check shares: is_active = False
   ```

6. **Wait for permanent deletion** (simulated)
   ```bash
   # Run cleanup task manually:
   # python manage.py cleanup_deleted_users
   # Verify user record deleted from database after 30 days
   ```

### Expected Results:
- ✅ Warning dialog shows before email sent
- ✅ Confirmation email sent with deletion link
- ✅ After confirmation: User logged out immediately
- ✅ Login fails: "Invalid credentials"
- ✅ Database: `deleted_at` timestamp set
- ✅ Shared content: All shares set to `is_active=False`
- ✅ After 30 days: User record permanently deleted

### API Verification:
```bash
# Initiate deletion
curl -X DELETE http://localhost:8000/api/account/ \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "detail": "Account deletion confirmation sent. Please check your email.",
#   "warning": "Your account and all associated data will be permanently deleted in 30 days."
# }

# Confirm deletion (use token from email)
curl -X POST http://localhost:8000/api/account/confirm-delete/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token": "xyz789...", "user_id": 123}'

# Response:
# {
#   "detail": "Account deleted successfully. Your data will be permanently removed in 30 days.",
#   "deleted_at": "2024-11-12T14:30:00Z",
#   "permanent_deletion_date": "2024-12-12T14:30:00Z"
# }
```

---

## Test Scenario 6: Pseudonym Display in Sharing

**Objective**: Verify shared content shows pseudonym, not email

### Steps:

1. **Create annotation as User A**
   ```bash
   # Login as User A (pseudonym: "user_a_2024")
   # Create a new map annotation
   ```

2. **Share annotation with User B**
   ```bash
   # Click "Share" on annotation
   # Enter User B's email
   # Click "Send Share"
   ```

3. **View as User B**
   ```bash
   # Login as User B
   # Navigate to shared annotations
   # Check "Shared by" field
   ```

4. **Verify pseudonym display**
   ```bash
   # "Shared by" should show: "user_a_2024"
   # User A's email should NOT be visible anywhere
   ```

5. **Update User A's pseudonym**
   ```bash
   # Login as User A
   # Change pseudonym to: "user_a_updated"
   # Save
   ```

6. **Verify sharing link still works**
   ```bash
   # Login as User B
   # Refresh shared annotations page
   # "Shared by" should now show: "user_a_updated"
   # Sharing link/reference unchanged
   ```

### Expected Results:
- ✅ Shared content shows sharer's pseudonym
- ✅ Email address never visible to recipient
- ✅ Pseudonym update changes display text
- ✅ Sharing links remain functional after pseudonym change

---

## Test Scenario 7: Accessibility Compliance

**Objective**: Verify WCAG 2.1 Level AA compliance for Account page

### Steps:

1. **Keyboard navigation**
   ```bash
   # Tab through all form fields
   # Verify logical tab order
   # Verify focus indicators visible (outline or highlight)
   ```

2. **Screen reader support**
   ```bash
   # Enable screen reader (NVDA/JAWS/VoiceOver)
   # Navigate to Account page
   # Verify all form labels announced
   # Verify error messages announced
   ```

3. **Color contrast**
   ```bash
   # Use browser dev tools color contrast analyzer
   # Verify text has ≥4.5:1 contrast ratio
   # Verify large text has ≥3:1 contrast ratio
   ```

4. **Form validation**
   ```bash
   # Submit invalid pseudonym
   # Verify error message associated with field (aria-describedby)
   # Verify error announced to screen reader
   ```

### Expected Results:
- ✅ Tab order: Pseudonym → Email → Password → Delete (logical flow)
- ✅ Focus indicators visible on all interactive elements
- ✅ Screen reader announces: "Pseudonym, edit text, required"
- ✅ Errors announced: "Error: Pseudonym cannot contain spaces"
- ✅ Color contrast meets 4.5:1 minimum
- ✅ No accessibility errors in axe DevTools

---

## Test Scenario 8: Responsive Design

**Objective**: Verify Account page responsive across viewports

### Steps:

1. **Mobile (320px width)**
   ```bash
   # Resize browser to 320px width
   # Verify form fields stack vertically
   # Verify buttons full-width
   # Verify text readable without horizontal scroll
   ```

2. **Tablet (768px width)**
   ```bash
   # Resize to 768px width
   # Verify layout adapts gracefully
   # Verify spacing appropriate
   ```

3. **Desktop (1920px width)**
   ```bash
   # Resize to 1920px width
   # Verify content not stretched too wide
   # Verify max-width constraint applied
   ```

### Expected Results:
- ✅ 320px: Single column layout, full-width buttons
- ✅ 768px: Comfortable spacing, readable font sizes
- ✅ 1920px: Content centered, max-width ~1200px
- ✅ No horizontal scroll at any viewport size

---

## Performance Verification

### API Response Times:

```bash
# Pseudonym validation
time curl -X POST http://localhost:8000/api/account/validate-pseudonym/ \
  -H "Content-Type: application/json" \
  -d '{"pseudonym": "test_user"}'

# Expected: <200ms p95

# Account update
time curl -X PATCH http://localhost:8000/api/account/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pseudonym": "updated_user"}'

# Expected: <500ms p95
```

---

## Database Verification

```sql
-- Check email encryption
SELECT id, pseudonym, email FROM users_user WHERE id = 123;
-- Email column should show encrypted bytes, not plain text

-- Check soft delete
SELECT id, pseudonym, deleted_at FROM users_user WHERE deleted_at IS NOT NULL;
-- Should show soft-deleted users with timestamp

-- Check pseudonym uniqueness
SELECT LOWER(pseudonym), COUNT(*) FROM users_user
GROUP BY LOWER(pseudonym)
HAVING COUNT(*) > 1;
-- Should return 0 rows (no duplicates)

-- Check audit log
SELECT * FROM users_accountlog
WHERE user_id = 123
ORDER BY timestamp DESC;
-- Should show log entries for all account operations
```

---

## Cleanup

```bash
# Reset test data
python manage.py flush --noinput
python manage.py migrate
python manage.py createsuperuser
```

---

## Success Criteria

All scenarios pass:
- [x] Pseudonym creation and display
- [x] Pseudonym validation rules
- [x] Email change with confirmation
- [x] Password change with verification
- [x] Account deletion with soft delete
- [x] Pseudonym display in sharing
- [x] Accessibility compliance
- [x] Responsive design
- [x] Performance targets met
- [x] Database integrity verified

**Estimated Total Test Time**: 30-45 minutes
