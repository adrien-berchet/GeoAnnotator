"""
Django management command to create test users for development.

Usage:
    python manage.py create_test_user
    python manage.py create_test_user --username testuser --email test@example.com
    python manage.py create_test_user --verified  # Auto-verify email
    python manage.py create_test_user --show-token  # Show confirmation link
"""

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import IntegrityError

from apps.authentication.models import EmailConfirmation
from apps.authentication.models import User
from apps.authentication.services import EmailConfirmationService


class Command(BaseCommand):
    help = "Create a test user for development and testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="testuser",
            help="Username for the test user (default: testuser)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="test@example.com",
            help="Email for the test user (default: test@example.com)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="Test1234",
            help="Password for the test user (default: Test1234)",
        )
        parser.add_argument(
            "--verified",
            action="store_true",
            help="Automatically verify the user's email (skip confirmation)",
        )
        parser.add_argument(
            "--show-token",
            action="store_true",
            help="Display the confirmation token and link",
        )
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete existing user with same email/username before creating",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        auto_verify = options["verified"]
        show_token = options["show_token"]
        delete_existing = options["delete_existing"]

        # Delete existing user if requested
        if delete_existing:
            deleted_count = 0
            # Delete by username
            try:
                existing_user = User.objects.get(username=username)
                existing_user.delete()
                deleted_count += 1
                self.stdout.write(f"  Deleted existing user with username: {username}")
            except User.DoesNotExist:
                pass

            # Delete by email
            try:
                email_hash = User.hash_email(email)
                existing_user = User.objects.get(email_hash=email_hash)
                if existing_user.username != username:  # Not already deleted
                    existing_user.delete()
                    deleted_count += 1
                    self.stdout.write(f"  Deleted existing user with email: {email}")
            except User.DoesNotExist:
                pass

            if deleted_count > 0:
                self.stdout.write("")

        # Create the user
        try:
            self.stdout.write(self.style.MIGRATE_HEADING("Creating test user..."))
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            self.stdout.write(self.style.SUCCESS(f"✓ User created successfully!"))
            self.stdout.write(f"  Username: {username}")
            self.stdout.write(f"  Email: {email}")
            self.stdout.write(f"  Password: {password}")
            self.stdout.write("")

            # Handle email verification
            if auto_verify:
                # Auto-verify the user
                user.is_verified = True
                user.save(update_fields=["is_verified"])
                self.stdout.write(self.style.SUCCESS("✓ Email automatically verified"))
                self.stdout.write(
                    self.style.WARNING("  → You can login immediately without email confirmation")
                )
            else:
                # Generate confirmation token
                token = EmailConfirmationService.generate_confirmation_token(
                    user, EmailConfirmation.REGISTRATION
                )

                # Show confirmation info
                self.stdout.write(self.style.WARNING("⚠ Email NOT verified"))
                self.stdout.write("  → User must confirm email before logging in")
                self.stdout.write("")

                if show_token or True:  # Always show token for convenience
                    from django.conf import settings

                    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
                    confirmation_link = f"{frontend_url}/confirm-email?token={token}"

                    self.stdout.write(self.style.MIGRATE_LABEL("Confirmation Details:"))
                    self.stdout.write(f"  Token: {token}")
                    self.stdout.write(f"  Link: {confirmation_link}")
                    self.stdout.write("")
                    self.stdout.write(
                        self.style.SUCCESS(
                            "  → Copy the link above and paste it in your browser to confirm the email"
                        )
                    )

                # Check if email will be sent
                email_backend = getattr(settings, "EMAIL_BACKEND", "")
                if "console" in email_backend.lower():
                    self.stdout.write("")
                    self.stdout.write(
                        self.style.WARNING(
                            "ℹ Email backend is set to 'console' - check your terminal for the confirmation email"
                        )
                    )
                elif "smtp" in email_backend.lower():
                    self.stdout.write("")
                    self.stdout.write(
                        self.style.SUCCESS(f"📧 Confirmation email sent to: {email}")
                    )
                    self.stdout.write("   Check your inbox!")

        except IntegrityError as e:
            error_msg = str(e)
            if "username" in error_msg.lower():
                raise CommandError(
                    f"User with username '{username}' already exists. "
                    f"Use --delete-existing to remove it first."
                )
            elif "email" in error_msg.lower():
                raise CommandError(
                    f"User with email '{email}' already exists. "
                    f"Use --delete-existing to remove it first."
                )
            else:
                raise CommandError(f"Error creating user: {e}")

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Quick Commands:"))
        self.stdout.write(f"  Login: POST /api/auth/login/")
        self.stdout.write(f'         {{"email": "{email}", "password": "{password}"}}')
        if not auto_verify:
            self.stdout.write(f"  Confirm: POST /api/auth/confirm-email/")
            self.stdout.write(f'           {{"token": "{token}"}}')
