# Test User Creation Command

Quick command to create test users during development.

## Basic Usage

```bash
# Create default test user (testuser / test@example.com / Test1234)
python manage.py create_test_user

# Or use the helper script
./create_test_user.sh
```

## Options

### Custom Credentials
```bash
python manage.py create_test_user \
  --username john \
  --email john@example.com \
  --password SecurePass123
```

### Auto-Verify Email
Skip email confirmation and mark user as verified immediately:
```bash
python manage.py create_test_user --verified
```

### Show Confirmation Token
Display the confirmation link (shown by default):
```bash
python manage.py create_test_user --show-token
```

### Delete Existing User
Delete user with same email/username before creating:
```bash
python manage.py create_test_user --delete-existing
```

## Examples

### Quick verified user for immediate login
```bash
python manage.py create_test_user --verified
# Can login right away without email confirmation
```

### Test full registration flow
```bash
python manage.py create_test_user
# Copy the confirmation link from output
# Paste in browser to confirm email
# Then login
```

### Create multiple test users
```bash
python manage.py create_test_user --username alice --email alice@test.com --verified
python manage.py create_test_user --username bob --email bob@test.com --verified
python manage.py create_test_user --username charlie --email charlie@test.com --verified
```

### Replace existing test user
```bash
python manage.py create_test_user --delete-existing --verified
```

## Output Example

```
Creating test user...
✓ User created successfully!
  Username: testuser
  Email: test@example.com
  Password: Test1234

⚠ Email NOT verified
  → User must confirm email before logging in

Confirmation Details:
  Token: abc123...
  Link: http://localhost:3000/confirm-email?token=abc123...

  → Copy the link above and paste it in your browser to confirm the email

Quick Commands:
  Login: POST /api/auth/login/
         {"email": "test@example.com", "password": "Test1234"}
  Confirm: POST /api/auth/confirm-email/
           {"token": "abc123..."}
```
