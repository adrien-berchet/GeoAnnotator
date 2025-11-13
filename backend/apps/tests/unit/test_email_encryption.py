"""
Unit test: Email encryption

Test the email encryption and decryption using Fernet.
"""

import pytest

from apps.authentication.models import User


@pytest.mark.django_db
class TestEmailEncryption:
    """Unit tests for email field encryption."""

    def test_email_encrypted_in_database(self, alice):
        """Test that email is encrypted when stored in database."""
        # Save with plaintext email
        alice.email = "test@example.com"
        alice.save()

        # Refresh from database to get raw encrypted value
        alice.refresh_from_db()

        # The encrypted email should not equal the plaintext
        # (When accessed through the model field, it's auto-decrypted)
        # So we need to check the raw database value
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE id = %s", [alice.id])
            raw_email = cursor.fetchone()[0]

        # Raw encrypted value should not be the plaintext
        assert raw_email != "test@example.com"
        # But accessing through model should return decrypted value
        assert alice.email == "test@example.com"

    def test_email_decrypted_when_accessed(self, alice):
        """Test that email is automatically decrypted when accessed."""
        plaintext_email = "alice@wonderland.com"
        alice.email = plaintext_email
        alice.save()

        # Reload from database
        alice.refresh_from_db()

        # Should return decrypted email
        assert alice.email == plaintext_email

    def test_email_encryption_roundtrip(self):
        """Test that email survives encryption/decryption roundtrip."""
        original_email = "roundtrip@test.com"

        user = User.objects.create_user(
            username="roundtrip_user", email=original_email, password="TestPass123!"
        )

        # Reload from database
        user.refresh_from_db()

        assert user.email == original_email

    def test_email_update_re_encrypts(self, alice):
        """Test that updating email re-encrypts with new value."""
        original_email = "original@example.com"
        new_email = "updated@example.com"

        alice.email = original_email
        alice.save()

        # Update email
        alice.email = new_email
        alice.save()

        # Reload and verify
        alice.refresh_from_db()
        assert alice.email == new_email

    def test_email_encryption_unique_per_save(self, alice):
        """Test that email encryption uses unique values (due to Fernet IV)."""
        email = "same@email.com"

        alice.email = email
        alice.save()

        # Get raw encrypted value
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE id = %s", [alice.id])
            encrypted1 = cursor.fetchone()[0]

        # Save again with same email
        alice.email = email
        alice.save()

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE id = %s", [alice.id])
            encrypted2 = cursor.fetchone()[0]

        # Encrypted values should differ (due to random IV in Fernet)
        # But both should decrypt to same value
        assert encrypted1 != encrypted2
        assert alice.email == email

    def test_multiple_users_different_emails_encrypted_differently(self):
        """Test that different emails for different users encrypt differently."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        user1 = User.objects.create_user(username="user1", email=email1, password="Pass123!")

        user2 = User.objects.create_user(username="user2", email=email2, password="Pass123!")

        # Get raw encrypted values
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT email FROM users WHERE id IN %s", [(user1.id, user2.id)]
            )
            encrypted_values = [row[0] for row in cursor.fetchall()]

        # Each should decrypt to their own email
        assert user1.email == email1
        assert user2.email == email2

        # And encrypted values should differ
        assert encrypted_values[0] != encrypted_values[1]

    def test_email_field_length_not_limited_by_encryption(self):
        """Test that long emails can be stored despite encryption expansion."""
        # Fernet encryption expands data, but field should handle it
        long_email = "very.long.email.address.with.many.parts@subdomain.example.com"

        user = User.objects.create_user(
            username="long_email_user", email=long_email, password="Pass123!"
        )

        user.refresh_from_db()
        assert user.email == long_email

    def test_email_encryption_preserves_special_characters(self):
        """Test that special characters in email are preserved."""
        special_email = "user+tag@example.co.uk"

        user = User.objects.create_user(
            username="special_char_user", email=special_email, password="Pass123!"
        )

        user.refresh_from_db()
        assert user.email == special_email

    def test_email_case_sensitivity_preserved(self):
        """Test that email domain is normalized to lowercase, but local part is preserved."""
        # Email addresses: domain is case-insensitive, local part may be case-sensitive
        # Django's normalize_email only lowercases the domain
        email = "MixedCase@Example.COM"

        user = User.objects.create_user(username="case_test", email=email, password="Pass123!")

        user.refresh_from_db()
        # Django normalizes only the domain to lowercase
        assert user.email == "MixedCase@example.com"
