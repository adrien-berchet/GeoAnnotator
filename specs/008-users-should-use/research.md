# Research: User Pseudonyms and Account Management

## Email Encryption in Database

**Decision**: Use Django's `Fernet` symmetric encryption via `django-fernet-fields` library

**Rationale**:
- Fernet provides authenticated encryption (confidentiality + integrity)
- Django-native solution integrates seamlessly with ORM
- Transparent encryption/decryption in model layer
- Keys managed via Django settings (environment variables in production)
- Performance overhead minimal for user account operations

**Alternatives Considered**:
- **PostgreSQL pgcrypto**: Requires database-level key management, complicates backups
- **AES manual implementation**: Higher complexity, error-prone, no integrity checks
- **Asymmetric encryption (RSA)**: Overkill for this use case, slower performance

**Implementation Notes**:
- Add `django-fernet-fields` to `requirements/base.txt`
- Store encryption key in environment variable `FERNET_KEY`
- Use `EncryptedEmailField` on User model
- Rotate keys periodically (document in operational runbook)

---

## Pseudonym Uniqueness Enforcement

**Decision**: Database-level unique constraint + application-level validation

**Rationale**:
- Database constraint prevents race conditions
- Application validation provides immediate user feedback
- Case-insensitive uniqueness via PostgreSQL `LOWER()` unique index
- Prevents duplicate pseudonyms regardless of capitalization

**Alternatives Considered**:
- **Application-only validation**: Vulnerable to race conditions between check and insert
- **Case-sensitive uniqueness**: Confusing UX ("Alice" vs "alice" allowed)
- **UUID-based pseudonyms**: Poor UX, defeats privacy-friendly naming purpose

**Implementation Notes**:
```sql
CREATE UNIQUE INDEX users_pseudonym_lower_unique
ON users_user (LOWER(pseudonym));
```
- Django migration with `RunSQL` for index creation
- Serializer validation with case-insensitive lookup before save
- Error message: "This pseudonym is already taken. Please choose a different one."

---

## Email Confirmation Token System

**Decision**: Use Django's built-in `PasswordResetTokenGenerator` pattern with custom timeout

**Rationale**:
- Well-tested, secure token generation (HMAC-based)
- Configurable expiry (30 minutes per requirements)
- Stateless (no database storage needed)
- Resistant to timing attacks and brute force

**Alternatives Considered**:
- **JWT tokens**: Overkill, requires library dependency, harder to invalidate
- **Random UUID in database**: Requires cleanup job for expired tokens, adds database load
- **django-simple-email-confirmation**: Third-party dependency for simple use case

**Implementation Notes**:
```python
class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.email}"

email_change_token = EmailChangeTokenGenerator()
```
- Store pending email in user session during confirmation flow
- Token includes user PK + timestamp + current email hash
- 30-minute expiry enforced in token validation
- Email sent via existing Django email backend

---

## Account Soft Delete Strategy

**Decision**: Add `deleted_at` timestamp field + scheduled cleanup task

**Rationale**:
- Simple implementation with single nullable timestamp field
- Query filtering via `deleted_at__isnull=True` for active users
- 30-day retention allows recovery from accidental deletions
- Scheduled task (Celery beat or cron) handles permanent deletion

**Alternatives Considered**:
- **Separate "deleted users" table**: Complicates foreign key relationships, schema migrations
- **Boolean `is_deleted` flag**: Loses deletion timestamp information, harder to audit
- **Immediate hard delete**: No recovery possible, higher support burden

**Implementation Notes**:
```python
# Model field
deleted_at = models.DateTimeField(null=True, blank=True)

# Manager for active users only
class ActiveUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

# Cleanup task (run daily)
@periodic_task(run_every=crontab(hour=2, minute=0))
def cleanup_deleted_users():
    threshold = timezone.now() - timedelta(days=30)
    User.objects.filter(deleted_at__lt=threshold).delete()
```
- Add custom manager for active users
- Update all queries to use `ActiveUserManager` by default
- Override `delete()` method to set `deleted_at` instead of hard delete
- Log deletions per FR-029 (audit trail)

---

## Pseudonym Validation Rules

**Decision**: Regex-based validation with clear error messages

**Rationale**:
- Regex provides precise character class matching
- Frontend and backend share same validation logic (export as JSON schema)
- Clear error messages guide users to compliant pseudonyms

**Validation Pattern**:
```regex
^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]{1,99}$
```

**Rules Breakdown**:
- Length: 1-99 characters (< 100 per requirements)
- Allowed: Letters (a-z, A-Z), digits (0-9), simple special characters
- Forbidden: Spaces (explicit exclusion per requirements)
- Unicode: Not supported initially (ASCII-only for simplicity)

**Alternatives Considered**:
- **Allowlist approach**: More restrictive, harder to communicate to users
- **Unicode support**: Complexity of normalization, homoglyph attacks, deferred to future iteration
- **Length limit 50**: Too restrictive, 100 is reasonable upper bound

**Implementation Notes**:
```python
# Serializer validation
def validate_pseudonym(self, value):
    if ' ' in value:
        raise ValidationError("Pseudonym cannot contain spaces.")
    if len(value) >= 100:
        raise ValidationError("Pseudonym must be less than 100 characters.")
    if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]+$', value):
        raise ValidationError(
            "Pseudonym can only contain letters, numbers, and simple special characters."
        )
    return value
```
- Frontend mirrors validation with same regex
- Display inline validation warnings as user types (debounced)
- Error messages match backend for consistency

---

## Password Change Verification

**Decision**: Django's built-in `check_password()` in serializer validation

**Rationale**:
- Standard Django pattern for password verification
- Secure password hashing (PBKDF2 by default)
- No need for custom implementation

**Implementation Notes**:
```python
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("Current password is incorrect.")
        return value
```
- Require old password in request payload
- Validate before allowing new password set
- Log password changes per FR-029

---

## Sharing Content Unsharing on Account Delete

**Decision**: Use Django signals (`pre_delete`) to trigger unsharing

**Rationale**:
- Decouples user deletion logic from sharing app
- Automatic execution on delete (no manual calls)
- Transactional safety (rolls back if unsharing fails)

**Implementation Notes**:
```python
# In apps/sharing/signals.py
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from apps.users.models import User
from apps.sharing.models import Share

@receiver(pre_delete, sender=User)
def unshare_user_content(sender, instance, **kwargs):
    """Unshare all content when user account is deleted."""
    if instance.deleted_at:  # Only for soft deletes
        Share.objects.filter(shared_by=instance).update(is_active=False)
```
- Signal fires when `deleted_at` is set (soft delete)
- Update shares to inactive immediately
- Actual share deletion happens in 30-day cleanup task
- Log unsharing actions for audit trail

---

## Frontend Pseudonym Display

**Decision**: Update user context/state management to expose pseudonym

**Rationale**:
- Centralized user data prevents inconsistent display
- Single source of truth for current user info
- Easy to update across all components

**Implementation Notes**:
```typescript
// services/accountService.ts
export interface UserAccount {
  id: number;
  pseudonym: string;
  email: string;  // Only for owner, plain text
  // ... other fields
}

// hooks/useAccount.ts
export function useAccount() {
  const { data: account, mutate } = useSWR<UserAccount>('/api/account/');

  const updatePseudonym = async (newPseudonym: string) => {
    await api.patch('/api/account/', { pseudonym: newPseudonym });
    mutate();  // Refresh account data
  };

  return { account, updatePseudonym };
}
```
- Menu bar component uses `account.pseudonym` instead of `account.email`
- Update sharing components to display sharer's pseudonym
- Cache user accounts to minimize API calls

---

## Email Confirmation Link Format

**Decision**: Standard URL with token query parameter

**Format**: `https://app.example.com/account/confirm-email?token={token}&user={user_id}`

**Rationale**:
- Simple, well-understood pattern
- Easy to generate and parse
- Works with standard email clients
- Frontend handles routing and API call

**Implementation Notes**:
```python
# Email template
confirmation_url = (
    f"{settings.FRONTEND_URL}/account/confirm-email"
    f"?token={token}&user={user.pk}"
)
```
```typescript
// Frontend route handler
export function ConfirmEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const userId = searchParams.get('user');

  useEffect(() => {
    api.post('/api/account/confirm-email/', { token, user_id: userId })
      .then(() => navigate('/account?email_confirmed=true'))
      .catch(err => setError(err.message));
  }, [token, userId]);
}
```

---

## Performance Optimization Strategies

**Decision**: Database indexing + query optimization

**Indexes Required**:
1. `users.pseudonym` (unique, lowercase) - pseudonym uniqueness checks
2. `users.email` (encrypted field) - authentication lookups
3. `users.deleted_at` - active user filtering

**Query Optimizations**:
- Use `select_related()` for user + profile joins
- Cache frequently accessed user data (pseudonyms in sharing lists)
- Batch pseudonym validation checks (if bulk import added later)

**Monitoring**:
- Django Debug Toolbar in development
- Application Performance Monitoring (APM) for p95 latency tracking
- Database query logging for slow queries (>100ms)

**Rationale**:
- Indexes prevent full table scans on large user bases
- Query optimization reduces database round trips
- Monitoring ensures performance targets met

---

## Accessibility Implementation

**Decision**: Follow ARIA best practices + automated testing

**Key Requirements (WCAG 2.1 Level AA)**:
- Keyboard navigation: Tab order logical, focus indicators visible
- Screen reader support: ARIA labels on form inputs, error announcements
- Color contrast: 4.5:1 minimum for text, 3:1 for large text
- Form validation: Errors announced, associated with inputs via `aria-describedby`

**Implementation Tools**:
- `eslint-plugin-jsx-a11y` for linting
- `axe-core` for automated testing
- Manual keyboard navigation testing
- Screen reader testing (NVDA/JAWS)

**Implementation Notes**:
```tsx
// Example: Pseudonym field with accessibility
<div>
  <label htmlFor="pseudonym">
    Pseudonym
    <span aria-label="required">*</span>
  </label>
  <input
    id="pseudonym"
    type="text"
    value={pseudonym}
    onChange={handleChange}
    aria-invalid={!!error}
    aria-describedby={error ? "pseudonym-error" : undefined}
  />
  {error && (
    <div id="pseudonym-error" role="alert" className="error">
      {error}
    </div>
  )}
</div>
```

---

## Summary

All technical unknowns resolved. Key decisions:
1. **Email encryption**: Fernet via django-fernet-fields
2. **Pseudonym uniqueness**: Database constraint + case-insensitive index
3. **Email confirmation**: HMAC token generator, 30-minute expiry
4. **Soft delete**: `deleted_at` timestamp + scheduled cleanup
5. **Validation**: Regex-based, <100 chars, no spaces
6. **Password verification**: Django `check_password()`
7. **Unsharing**: Django signals on pre_delete
8. **Frontend display**: Centralized account state management
9. **Performance**: Strategic indexing + query optimization
10. **Accessibility**: ARIA + automated testing

Ready for Phase 1 design.
