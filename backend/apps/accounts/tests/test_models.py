


"""
Tests for the accounts User model.
"""

import pytest

from apps.accounts.models import User

from .factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self):
        """A user can be created successfully."""
        user = UserFactory()

        assert user.pk is not None
        assert user.username.startswith("testuser")
        assert user.role == User.Role.STUDENT
        assert user.is_verified is False
        assert user.is_active is True

    def test_user_string_representation(self):
        """The string representation is the username."""
        user = UserFactory(username="john")

        assert str(user) == "john"

    def test_default_role_is_student(self):
        """New users default to the student role."""
        user = UserFactory()

        assert user.role == User.Role.STUDENT

    def test_default_verification_status_is_false(self):
        """New users are unverified by default."""
        user = UserFactory()

        assert user.is_verified is False

    def test_created_at_is_set(self):
        """created_at is automatically populated."""
        user = UserFactory()

        assert user.created_at is not None

    def test_updated_at_is_set(self):
        """updated_at is automatically populated."""
        user = UserFactory()

        assert user.updated_at is not None

    def test_password_is_hashed(self):
        """Passwords are never stored in plaintext."""
        user = UserFactory(password="StrongPassword123!")

        assert user.password != "StrongPassword123!"
        assert user.check_password("StrongPassword123!")

    def test_role_choices(self):
        """The configured roles are available."""
        assert User.Role.STUDENT == "student"
        assert User.Role.INSTRUCTOR == "instructor"
        assert User.Role.ADMIN == "admin"



