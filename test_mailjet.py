#!/usr/bin/env python
"""
Test Mailjet Email Backend locally.

Run this script to verify Mailjet configuration before deploying.

Usage:
    export MAILJET_API_KEY="your_api_key"
    export MAILJET_SECRET_KEY="your_secret_key"
    export DEFAULT_FROM_EMAIL="verified@sender.com"
    python test_mailjet.py
"""

import os
import sys

# Add Django project to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django
from django.core.mail import send_mail

django.setup()


def test_mailjet_email():
    """Send a test email via Mailjet API."""
    # Check required environment variables
    required_vars = ["MAILJET_API_KEY", "MAILJET_SECRET_KEY", "DEFAULT_FROM_EMAIL"]
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet them with:")
        print("  export MAILJET_API_KEY='your_api_key'")
        print("  export MAILJET_SECRET_KEY='your_secret_key'")
        print("  export DEFAULT_FROM_EMAIL='verified@sender.com'")
        sys.exit(1)

    print("✓ Environment variables configured")
    print(f"  API Key: {os.environ['MAILJET_API_KEY'][:10]}...")
    print(f"  From: {os.environ['DEFAULT_FROM_EMAIL']}")
    print()

    # Get recipient email
    recipient = input("Enter recipient email address: ").strip()
    if not recipient or "@" not in recipient:
        print("❌ Invalid email address")
        sys.exit(1)

    print(f"\n🚀 Sending test email to {recipient}...")

    try:
        # Configure backend for this test
        from django.conf import settings

        settings.EMAIL_BACKEND = "apps.core.mailjet_backend.MailjetBackend"
        settings.MAILJET_API_KEY = os.environ["MAILJET_API_KEY"]
        settings.MAILJET_SECRET_KEY = os.environ["MAILJET_SECRET_KEY"]
        settings.DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]

        # Send test email
        num_sent = send_mail(
            subject="GeoAnnotator Test Email - Mailjet API",
            message=(
                "This is a test email from GeoAnnotator.\n\n"
                "If you received this, the Mailjet API integration is working correctly!\n\n"
                "Configuration:\n"
                f"- Backend: {settings.EMAIL_BACKEND}\n"
                f"- From: {settings.DEFAULT_FROM_EMAIL}\n"
                f"- API: Mailjet HTTP v3.1\n\n"
                "You can now deploy to production with confidence.\n\n"
                "Best regards,\n"
                "The GeoAnnotator Team"
            ),
            from_email=os.environ["DEFAULT_FROM_EMAIL"],
            recipient_list=[recipient],
            html_message=(
                "<!DOCTYPE html>"
                "<html><body style='font-family: Arial, sans-serif;'>"
                "<h2 style='color: #4CAF50;'>✓ Mailjet API Test Successful!</h2>"
                "<p>This is a test email from <strong>GeoAnnotator</strong>.</p>"
                "<p>If you received this, the Mailjet API integration is working correctly!</p>"
                "<h3>Configuration:</h3>"
                "<ul>"
                f"<li><strong>Backend:</strong> {settings.EMAIL_BACKEND}</li>"
                f"<li><strong>From:</strong> {settings.DEFAULT_FROM_EMAIL}</li>"
                "<li><strong>API:</strong> Mailjet HTTP v3.1</li>"
                "</ul>"
                "<p>You can now deploy to production with confidence.</p>"
                "<p>Best regards,<br><strong>The GeoAnnotator Team</strong></p>"
                "</body></html>"
            ),
            fail_silently=False,
        )

        if num_sent > 0:
            print("\n✅ Email sent successfully via Mailjet API!")
            print(f"   {num_sent} message(s) sent")
            print(f"\nCheck {recipient} inbox (and spam folder)")
            print("\n🎉 Mailjet configuration is working!")
            print("\nNext steps:")
            print("  1. Set environment variables on Render.com")
            print("  2. Deploy your application")
            print("  3. Monitor email delivery in Mailjet dashboard")
        else:
            print("\n⚠️ No email was sent (num_sent=0)")

    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_mailjet_email()
