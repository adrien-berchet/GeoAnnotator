#!/usr/bin/env python
"""Quick test to verify services and views work."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.authentication.services import AuthenticationService
from apps.authentication.models import User

# Test 1: Create user
print("Test 1: Create user...")
try:
    # Clean up first
    User.objects.filter(email='test@example.com').delete()

    user = AuthenticationService.create_user(
        email='test@example.com',
        password='SecurePass123'
    )
    print(f"✅ User created: {user.email}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Generate tokens
print("\nTest 2: Generate tokens...")
try:
    tokens = AuthenticationService.generate_tokens(user)
    print(f"✅ Tokens generated:")
    print(f"   - Access token: {tokens['access'][:50]}...")
    print(f"   - Refresh token: {tokens['refresh'][:50]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Authenticate user
print("\nTest 3: Authenticate user...")
try:
    auth_user = AuthenticationService.authenticate_user(
        email='test@example.com',
        password='SecurePass123'
    )
    if auth_user:
        print(f"✅ User authenticated: {auth_user.email}")
    else:
        print("❌ Authentication failed")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Check URLs
print("\nTest 4: Check URL routing...")
try:
    from django.urls import reverse
    urls = [
        ('auth:register', '/api/auth/register/'),
        ('auth:login', '/api/auth/login/'),
        ('auth:refresh', '/api/auth/refresh/'),
        ('auth:me', '/api/auth/me/'),
    ]

    for name, expected in urls:
        try:
            url = reverse(name)
            status = '✅' if url == expected else f'⚠️  (got {url})'
            print(f"   {name}: {status}")
        except Exception as e:
            print(f"   {name}: ❌ {e}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== Tests completed ===")
