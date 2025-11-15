"""
Django management command to test email configuration and SMTP connection.

Usage:
    python manage.py test_email
    python manage.py test_email --to your-email@example.com
"""

import sys

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test email configuration and SMTP connection"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            default="test@example.com",
            help="Email address to send test email to",
        )

    def handle(self, *args, **options):
        recipient = options["to"]

        self.stdout.write(self.style.MIGRATE_HEADING("Email Configuration Test"))
        self.stdout.write("")

        # Display current configuration
        self.stdout.write(self.style.MIGRATE_LABEL("Current Email Settings:"))
        self.stdout.write(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"  EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
        self.stdout.write(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")

        # Show password status (not the actual password)
        password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
        if password:
            self.stdout.write(f"  EMAIL_HOST_PASSWORD: {password} (set)")
        else:
            self.stdout.write("  EMAIL_HOST_PASSWORD: Not set")

        self.stdout.write(
            f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}"
        )
        self.stdout.write("")

        # Check if using console backend
        if "console" in settings.EMAIL_BACKEND.lower():
            self.stdout.write(
                self.style.WARNING(
                    "⚠ Console backend detected - emails will be printed to console, not sent via SMTP"
                )
            )
            self.stdout.write("")

        # Try to send test email
        self.stdout.write(self.style.MIGRATE_LABEL("Attempting to send test email..."))
        self.stdout.write(f"  To: {recipient}")
        self.stdout.write("")

        try:
            result = send_mail(
                subject="GeoAnnotator Email Test",
                message=(
                    "This is a test email from GeoAnnotator.\n\n"
                    "If you receive this, your email configuration is working correctly!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )

            if result == 1:
                self.stdout.write(self.style.SUCCESS("✓ Email sent successfully!"))

                if "console" not in settings.EMAIL_BACKEND.lower():
                    self.stdout.write("")
                    self.stdout.write("Please check your inbox (and spam folder).")
                    self.stdout.write(
                        "If you don't receive the email, check the configuration above."
                    )
                else:
                    self.stdout.write("")
                    self.stdout.write(
                        "The email should be printed in your console/terminal output."
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Email sending returned unexpected result: {result}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR("✗ Email sending failed!"))
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            self.stdout.write("")

            # Provide helpful hints based on error
            error_str = str(e).lower()

            if "authentication" in error_str or "username" in error_str or "password" in error_str:
                self.stdout.write(self.style.WARNING("Possible causes:"))
                self.stdout.write("  - Incorrect EMAIL_HOST_USER or EMAIL_HOST_PASSWORD")
                self.stdout.write(
                    "  - For Gmail: Make sure you're using an App Password, not your regular password"
                )
                self.stdout.write(
                    "  - For Gmail: App Passwords require 2-Factor Authentication to be enabled"
                )
                self.stdout.write(
                    "  - Get App Password at: https://myaccount.google.com/apppasswords"
                )

            elif "connection" in error_str or "timeout" in error_str:
                self.stdout.write(self.style.WARNING("Possible causes:"))
                self.stdout.write("  - Incorrect EMAIL_HOST or EMAIL_PORT")
                self.stdout.write("  - Firewall blocking SMTP connections")
                self.stdout.write("  - Check EMAIL_USE_TLS and EMAIL_USE_SSL settings")

            elif "ssl" in error_str or "tls" in error_str:
                self.stdout.write(self.style.WARNING("Possible causes:"))
                self.stdout.write("  - EMAIL_USE_TLS or EMAIL_USE_SSL misconfigured")
                self.stdout.write("  - For Gmail: Use EMAIL_USE_TLS=True with port 587")
                self.stdout.write("  - Or use EMAIL_USE_SSL=True with port 465")

            sys.exit(1)

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Test Complete"))
