"""
Unit test: Username validation logic

Test the username validation service function.
"""

import pytest

from apps.authentication.services import validate_username


@pytest.mark.django_db
class TestUsernameValidation:
    """Unit tests for username validation logic."""

    def test_validate_username_valid_and_available(self):
        """Test that valid and available username passes validation."""
        result = validate_username("valid_username_123")

        assert result["valid"] is True
        assert result["available"] is True
        assert result["errors"] == []

    def test_validate_username_with_spaces_invalid(self):
        """Test that username with spaces is invalid."""
        result = validate_username("invalid user")

        assert result["valid"] is False
        assert result["available"] is None
        assert "errors" in result and len(result["errors"]) > 0
        assert any("space" in error.lower() for error in result["errors"])

    def test_validate_username_empty_invalid(self):
        """Test that empty username is invalid."""
        result = validate_username("")

        assert result["valid"] is False
        assert result["available"] is None

    def test_validate_username_too_long_invalid(self):
        """Test that username over 100 characters is invalid."""
        long_username = "a" * 101
        result = validate_username(long_username)

        assert result["valid"] is False
        assert result["available"] is None

    def test_validate_username_exactly_100_chars_valid(self):
        """Test that username with exactly 100 characters is valid."""
        username = "a" * 100
        result = validate_username(username)

        assert result["valid"] is True

    def test_validate_username_one_char_invalid(self):
        """Test that single character username is invalid (minimum 3 chars)."""
        result = validate_username("a")

        assert result["valid"] is False

    def test_validate_username_special_characters_valid(self):
        """Test that username with allowed special characters is valid (only _ and -)."""
        result = validate_username("user_2024-test")

        assert result["valid"] is True

    def test_validate_username_alphanumeric_valid(self):
        """Test that alphanumeric username is valid."""
        result = validate_username("User123")

        assert result["valid"] is True

    def test_validate_username_duplicate_returns_unavailable(self, alice):
        """Test that duplicate username is marked as unavailable."""
        alice.username = "alice_unique"
        alice.save()

        result = validate_username("alice_unique")

        assert result["valid"] is True
        assert result["available"] is False
        assert len(result["errors"]) > 0
        assert any("taken" in error.lower() for error in result["errors"])

    def test_validate_username_case_insensitive_duplicate(self, alice):
        """Test that duplicate check is case-insensitive."""
        alice.username = "AliceWonderland"
        alice.save()

        # Try lowercase version
        result = validate_username("alicewonderland")

        assert result["valid"] is True
        assert result["available"] is False

    def test_validate_username_multiple_spaces_invalid(self):
        """Test that username with multiple spaces is invalid."""
        result = validate_username("many   spaces   here")

        assert result["valid"] is False

    def test_validate_username_leading_trailing_spaces_invalid(self):
        """Test that username with leading/trailing spaces is invalid."""
        result = validate_username(" spacesaround ")

        assert result["valid"] is False

    def test_validate_username_underscore_valid(self):
        """Test that underscores are allowed."""
        result = validate_username("user_name_123")

        assert result["valid"] is True

    def test_validate_username_hyphen_valid(self):
        """Test that hyphens are allowed."""
        result = validate_username("user-name-123")

        assert result["valid"] is True

    def test_validate_username_mixed_case_valid(self):
        """Test that mixed case is allowed."""
        result = validate_username("UserName123")

        assert result["valid"] is True
