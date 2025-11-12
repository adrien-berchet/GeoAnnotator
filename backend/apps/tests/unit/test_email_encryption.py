"""
Unit test: Email encryption

Test the email encryption and decryption using Fernet.
"""

import pytest

from apps.authentication.models import User


@pytest.mark.django_db
class TestEmailEncryption:
    """Unit tests for email field encryption."""

    def test_email_encrypted_in_database(self, user_alice):
        """Test that email is encrypted when stored in database."""
        # Save with plaintext email
        user_alice.email = "test@example.com"
        user_alice.save()

        # Refresh from database to get raw encrypted value
        user_alice.refresh_from_db()

        # The encrypted email should not equal the plaintext
        # (When accessed through the model field, it's auto-decrypted)
        # So we need to check the raw database value
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM authentication_user WHERE id = %s", [user_alice.id])
            raw_email = cursor.fetchone()[0]

        # Raw encrypted value should not be the plaintext
        assert raw_email != "test@example.com"
        # But accessing through model should return decrypted value
        assert user_alice.email == "test@example.com"

    def test_email_decrypted_when_accessed(self, user_alice):
        """Test that email is automatically decrypted when accessed."""
        plaintext_email = "alice@wonderland.com"
        user_alice.email = plaintext_email
        user_alice.save()

        # Reload from database
        user_alice.refresh_from_db()

        # Should return decrypted email
        assert user_alice.email == plaintext_email

    def test_email_encryption_roundtrip(self):
        """Test that email survives encryption/decryption roundtrip."""
        original_email = "roundtrip@test.com"

        user = User.objects.create_user(
            email=original_email, password="TestPass123!", pseudonym="roundtrip_user"
        )

        # Reload from database
        user.refresh_from_db()

        assert user.email == original_email

    def test_email_update_re_encrypts(self, user_alice):
        """Test that updating email re-encrypts with new value."""
        original_email = "original@example.com"
        new_email = "updated@example.com"

        user_alice.email = original_email
        user_alice.save()

        # Update email
        user_alice.email = new_email
        user_alice.save()

        # Reload and verify
        user_alice.refresh_from_db()
        assert user_alice.email == new_email

    def test_email_encryption_unique_per_save(self, user_alice):
        """Test that email encryption uses unique values (due to Fernet IV)."""
        email = "same@email.com"

        user_alice.email = email
        user_alice.save()

        # Get raw encrypted value
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM authentication_user WHERE id = %s", [user_alice.id])
            encrypted1 = cursor.fetchone()[0]

        # Save again with same email
        user_alice.email = email
        user_alice.save()

        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM authentication_user WHERE id = %s", [user_alice.id])
            encrypted2 = cursor.fetchone()[0]

        # Encrypted values should differ (due to random IV in Fernet)
        # But both should decrypt to same value
        assert encrypted1 != encrypted2
        assert user_alice.email == email

    def test_multiple_users_same_email_encrypted_differently(self):
        """Test that same email for different users encrypts differently."""
        email = "shared@example.com"

        user1 = User.objects.create_user(email=email, password="Pass123!", pseudonym="user1")

        user2 = User.objects.create_user(email=email, password="Pass123!", pseudonym="user2")

        # Get raw encrypted values
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT email FROM authentication_user WHERE id IN %s", [(user1.id, user2.id)]
            )
            encrypted_values = [row[0] for row in cursor.fetchall()]

        # Both should decrypt to same email
        assert user1.email == email
        assert user2.email == email

        # But encrypted values should differ
        assert encrypted_values[0] != encrypted_values[1]

    def test_email_field_length_not_limited_by_encryption(self):
        """Test that long emails can be stored despite encryption expansion."""
        # Fernet encryption expands data, but field should handle it
        long_email = "very.long.email.address.with.many.parts@subdomain.example.com"

        user = User.objects.create_user(
            email=long_email, password="Pass123!", pseudonym="long_email_user"
        )

        user.refresh_from_db()
        assert user.email == long_email

    def test_email_encryption_preserves_special_characters(self):
        """Test that special characters in email are preserved."""
        special_email = "user+tag@example.co.uk"

        user = User.objects.create_user(
            email=special_email, password="Pass123!", pseudonym="special_char_user"
        )

        user.refresh_from_db()
        assert user.email == special_email

    def test_email_case_sensitivity_preserved(self):
        """Test that email case is preserved through encryption."""
        # Note: Email addresses are case-insensitive per RFC, but we store as-is
        email = "MixedCase@Example.COM"

        user = User.objects.create_user(email=email, password="Pass123!", pseudonym="case_test")

        user.refresh_from_db()
        assert user.email == email
