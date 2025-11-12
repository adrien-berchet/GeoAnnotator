"""
Unit test: Pseudonym validation logic

Test the pseudonym validation service function.
"""

import pytest

from apps.authentication.services import validate_pseudonym


@pytest.mark.django_db
class TestPseudonymValidation:
    """Unit tests for pseudonym validation logic."""

    def test_validate_pseudonym_valid_and_available(self):
        """Test that valid and available pseudonym passes validation."""
        result = validate_pseudonym("valid_pseudonym_123")

        assert result["valid"] is True
        assert result["available"] is True
        assert "error" not in result or result["error"] is None

    def test_validate_pseudonym_with_spaces_invalid(self):
        """Test that pseudonym with spaces is invalid."""
        result = validate_pseudonym("invalid pseudo")

        assert result["valid"] is False
        assert result["available"] is None
        assert result["error"] is not None
        assert "space" in result["error"].lower()

    def test_validate_pseudonym_empty_invalid(self):
        """Test that empty pseudonym is invalid."""
        result = validate_pseudonym("")

        assert result["valid"] is False
        assert result["available"] is None

    def test_validate_pseudonym_too_long_invalid(self):
        """Test that pseudonym over 99 characters is invalid."""
        long_pseudonym = "a" * 100
        result = validate_pseudonym(long_pseudonym)

        assert result["valid"] is False
        assert result["available"] is None

    def test_validate_pseudonym_exactly_99_chars_valid(self):
        """Test that pseudonym with exactly 99 characters is valid."""
        pseudonym = "a" * 99
        result = validate_pseudonym(pseudonym)

        assert result["valid"] is True

    def test_validate_pseudonym_one_char_valid(self):
        """Test that single character pseudonym is valid."""
        result = validate_pseudonym("a")

        assert result["valid"] is True

    def test_validate_pseudonym_special_characters_valid(self):
        """Test that pseudonym with allowed special characters is valid."""
        result = validate_pseudonym("user_2024!@#$%^&*()")

        assert result["valid"] is True

    def test_validate_pseudonym_alphanumeric_valid(self):
        """Test that alphanumeric pseudonym is valid."""
        result = validate_pseudonym("User123")

        assert result["valid"] is True

    def test_validate_pseudonym_duplicate_returns_unavailable(self, user_alice):
        """Test that duplicate pseudonym is marked as unavailable."""
        user_alice.pseudonym = "alice_unique"
        user_alice.save()

        result = validate_pseudonym("alice_unique")

        assert result["valid"] is True
        assert result["available"] is False
        assert "taken" in result["error"].lower()

    def test_validate_pseudonym_case_insensitive_duplicate(self, user_alice):
        """Test that duplicate check is case-insensitive."""
        user_alice.pseudonym = "AliceWonderland"
        user_alice.save()

        # Try lowercase version
        result = validate_pseudonym("alicewonderland")

        assert result["valid"] is True
        assert result["available"] is False

    def test_validate_pseudonym_multiple_spaces_invalid(self):
        """Test that pseudonym with multiple spaces is invalid."""
        result = validate_pseudonym("many   spaces   here")

        assert result["valid"] is False

    def test_validate_pseudonym_leading_trailing_spaces_invalid(self):
        """Test that pseudonym with leading/trailing spaces is invalid."""
        result = validate_pseudonym(" spacesaround ")

        assert result["valid"] is False

    def test_validate_pseudonym_underscore_valid(self):
        """Test that underscores are allowed."""
        result = validate_pseudonym("user_name_123")

        assert result["valid"] is True

    def test_validate_pseudonym_hyphen_valid(self):
        """Test that hyphens are allowed."""
        result = validate_pseudonym("user-name-123")

        assert result["valid"] is True

    def test_validate_pseudonym_mixed_case_valid(self):
        """Test that mixed case is allowed."""
        result = validate_pseudonym("UserName123")

        assert result["valid"] is True
