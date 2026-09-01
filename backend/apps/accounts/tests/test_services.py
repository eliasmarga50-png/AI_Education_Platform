



"""
Tests for the accounts service layer.
"""

import pytest

from apps.accounts.models import User
from apps.accounts.services import AccountService

from .factories import UserFactory


@pytest.mark.django_db
class TestAccountService:
    """Tests for AccountService."""

    def test_create_user(self):
        """The service creates a user successfully."""
        user = AccountService.create_user(
            username="newuser",
            email="newuser@example.com",
            password="StrongPassword123!",
        )

        assert user.pk is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == User.Role.STUDENT
        assert user.check_password("StrongPassword123!")

    def test_create_user_requires_username(self):
        """Username is required when creating a user."""
        with pytest.raises(ValueError, match="username"):
            AccountService.create_user(
                username="",
                password="StrongPassword123!",
            )

    def test_create_user_requires_password(self):
        """Password is required when creating a user."""
        with pytest.raises(ValueError, match="password"):
            AccountService.create_user(
                username="newuser",
                password="",
            )

    def test_create_user_accepts_role(self):
        """The service can create a user with a supplied role."""
        user = AccountService.create_user(
            username="instructor",
            password="StrongPassword123!",
            role=User.Role.INSTRUCTOR,
        )

        assert user.role == User.Role.INSTRUCTOR

    def test_authenticate_user_with_valid_credentials(self):
        """Valid credentials return the authenticated user."""
        UserFactory(
            username="john",
            password="StrongPassword123!",
        )

        user = AccountService.authenticate_user(
            username="john",
            password="StrongPassword123!",
        )

        assert user is not None
        assert user.username == "john"

    def test_authenticate_user_with_invalid_password(self):
        """Invalid credentials return None."""
        UserFactory(
            username="john",
            password="StrongPassword123!",
        )

        user = AccountService.authenticate_user(
            username="john",
            password="WrongPassword123!",
        )

        assert user is None

    def test_authenticate_user_with_missing_credentials(self):
        """Missing credentials return None."""
        assert (
            AccountService.authenticate_user(
                username="",
                password="",
            )
            is None
        )

    def test_get_user_by_id(self):
        """A user can be retrieved by primary key."""
        user = UserFactory()

        result = AccountService.get_user_by_id(
            user_id=user.pk,
        )

        assert result == user

    def test_get_user_by_id_returns_none_for_missing_user(self):
        """Missing user IDs return None."""
        result = AccountService.get_user_by_id(
            user_id=999999,
        )

        assert result is None

    def test_get_user_by_username(self):
        """A user can be retrieved by username."""
        user = UserFactory(username="john")

        result = AccountService.get_user_by_username(
            username="john",
        )

        assert result == user

    def test_get_user_by_username_returns_none_for_empty_username(self):
        """Empty usernames return None."""
        assert AccountService.get_user_by_username(username="") is None

    def test_get_user_by_email(self):
        """A user can be retrieved by email."""
        user = UserFactory(
            email="john@example.com",
        )

        result = AccountService.get_user_by_email(
            email="john@example.com",
        )

        assert result == user

    def test_get_user_by_email_returns_none_for_empty_email(self):
        """Empty emails return None."""
        assert AccountService.get_user_by_email(email="") is None

    def test_update_user(self):
        """User profile fields can be updated."""
        user = UserFactory(first_name="Old")

        result = AccountService.update_user(
            user=user,
            first_name="New",
            last_name="Name",
        )

        result.refresh_from_db()

        assert result.first_name == "New"
        assert result.last_name == "Name"

    def test_update_user_without_fields(self):
        """Updating without fields leaves the user unchanged."""
        user = UserFactory(first_name="Original")

        result = AccountService.update_user(user=user)

        assert result == user
        assert result.first_name == "Original"

    def test_change_password(self):
        """A user's password can be changed securely."""
        user = UserFactory(
            password="OldPassword123!",
        )

        AccountService.change_password(
            user=user,
            new_password="NewPassword123!",
        )

        user.refresh_from_db()

        assert user.check_password("NewPassword123!")
        assert not user.check_password("OldPassword123!")

    def test_change_password_requires_password(self):
        """An empty new password is rejected."""
        user = UserFactory()

        with pytest.raises(ValueError, match="password"):
            AccountService.change_password(
                user=user,
                new_password="",
            )

    def test_deactivate_user(self):
        """A user can be deactivated."""
        user = UserFactory(is_active=True)

        AccountService.deactivate_user(user=user)

        user.refresh_from_db()

        assert user.is_active is False

    def test_activate_user(self):
        """A user can be activated."""
        user = UserFactory(is_active=False)

        AccountService.activate_user(user=user)

        user.refresh_from_db()

        assert user.is_active is True

    def test_verify_user(self):
        """A user can be verified."""
        user = UserFactory(is_verified=False)

        AccountService.verify_user(user=user)

        user.refresh_from_db()

        assert user.is_verified is True

    def test_unverify_user(self):
        """A user can be marked as unverified."""
        user = UserFactory(is_verified=True)

        AccountService.unverify_user(user=user)

        user.refresh_from_db()

        assert user.is_verified is False

