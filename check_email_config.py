#!/usr/bin/env python
"""
Check email configuration in production.

Usage:
    python check_email_config.py

Or with specific Django settings:
    DJANGO_SETTINGS_MODULE=config.settings.production python check_email_config.py
"""

import os
import sys

# Add Django project to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Use production settings by default
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
from django.conf import settings

django.setup()


def check_email_config():
    """Display current email configuration."""
    print("=" * 60)
    print("EMAIL CONFIGURATION CHECK")
    print("=" * 60)
    print()

    # Django settings module
    print(f"📋 Settings Module: {settings.SETTINGS_MODULE}")
    print()

    # Email backend
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print()

    # Check backend type
    if "mailjet" in settings.EMAIL_BACKEND.lower():
        print("✅ Backend Type: Mailjet HTTP API")
        print()
        print("Mailjet Configuration:")
        print("-" * 60)

        # Check API credentials
        api_key = getattr(settings, "MAILJET_API_KEY", None)
        secret_key = getattr(settings, "MAILJET_SECRET_KEY", None)

        if api_key:
            print(f"  ✅ MAILJET_API_KEY: {api_key[:8]}... (configured)")
        else:
            print("  ❌ MAILJET_API_KEY: Not configured")

        if secret_key:
            print(f"  ✅ MAILJET_SECRET_KEY: {secret_key[:8]}... (configured)")
        else:
            print("  ❌ MAILJET_SECRET_KEY: Not configured")

        # Default sender
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Not set")
        from_name = getattr(settings, "DEFAULT_FROM_NAME", "Not set")
        print(f"  📬 DEFAULT_FROM_EMAIL: {from_email}")
        print(f"  👤 DEFAULT_FROM_NAME: {from_name}")

        print()

        # Overall status
        if api_key and secret_key:
            print("🎉 Status: CONFIGURED ✅")
            print()
            print("Next steps:")
            print("  1. Verify sender address in Mailjet dashboard")
            print("  2. Test sending email via admin panel or API")
            print("  3. Check Mailjet dashboard for delivery status")
        else:
            print("⚠️  Status: MISSING CREDENTIALS ❌")
            print()
            print("Required environment variables:")
            print("  export MAILJET_API_KEY='your_api_key'")
            print("  export MAILJET_SECRET_KEY='your_secret_key'")
            print("  export DEFAULT_FROM_EMAIL='verified@sender.com'")

    elif "smtp" in settings.EMAIL_BACKEND.lower():
        print("📮 Backend Type: SMTP")
        print()
        print("SMTP Configuration:")
        print("-" * 60)

        email_host = getattr(settings, "EMAIL_HOST", "Not set")
        email_port = getattr(settings, "EMAIL_PORT", "Not set")
        email_use_tls = getattr(settings, "EMAIL_USE_TLS", False)
        email_user = getattr(settings, "EMAIL_HOST_USER", None)

        print(f"  🌐 EMAIL_HOST: {email_host}")
        print(f"  🔌 EMAIL_PORT: {email_port}")
        print(f"  🔒 EMAIL_USE_TLS: {email_use_tls}")

        if email_user:
            print(f"  ✅ EMAIL_HOST_USER: {email_user}")
        else:
            print("  ❌ EMAIL_HOST_USER: Not configured")

        print()

        if email_user:
            print("⚠️  Warning: SMTP may be blocked on some platforms (Render.com)")
            print("   Consider switching to Mailjet HTTP API")
        else:
            print("❌ Status: MISSING CREDENTIALS")

    elif "console" in settings.EMAIL_BACKEND.lower():
        print("🖥️  Backend Type: Console (Development Only)")
        print()
        print("⚠️  Emails will be printed to console, not sent")

    else:
        print(f"❓ Backend Type: Unknown ({settings.EMAIL_BACKEND})")

    print()
    print("=" * 60)


if __name__ == "__main__":
    check_email_config()
