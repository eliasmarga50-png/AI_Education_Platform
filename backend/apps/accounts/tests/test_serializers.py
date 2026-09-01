
"""
Tests for accounts serializers.
"""

import pytest

from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

from .factories import UserFactory


@pytest.mark.django_db
class TestUserSerializer:
    """Tests for UserSerializer."""

    def test_serializes_user(self):
        """A user is serialized with the expected public fields."""
        user = UserFactory(
            username="john",
            email="john@example.com",
            first_name="John",
            last_name="Doe",
        )

        serializer = UserSerializer(user)

        assert serializer.data["id"] == user.id
        assert serializer.data["username"] == "john"
        assert serializer.data["email"] == "john@example.com"
        assert serializer.data["first_name"] == "John"
        assert serializer.data["last_name"] == "Doe"
        assert serializer.data["role"] == User.Role.STUDENT
        assert serializer.data["is_verified"] is False

    def test_sensitive_fields_are_not_exposed(self):
        """Password and privilege fields are not exposed."""
        user = UserFactory()

        data = UserSerializer(user).data

        assert "password" not in data
        assert "is_staff" not in data
        assert "is_superuser" not in data


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Tests for UserRegistrationSerializer."""

    def valid_data(self, **overrides):
        data = {
            "username": "newstudent",
            "email": "student@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "New",
            "last_name": "Student",
        }
        data.update(overrides)
        return data

    def test_valid_registration(self):
        """Valid registration data is accepted."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(),
        )

        assert serializer.is_valid(), serializer.errors

    def test_creates_user(self):
        """Valid data creates a user through the service layer."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(),
        )

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.pk is not None
        assert user.username == "newstudent"
        assert user.email == "student@example.com"
        assert user.role == User.Role.STUDENT
        assert user.check_password("StrongPassword123!")

    def test_password_is_not_returned(self):
        """Passwords are write-only."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(),
        )

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert "password" not in serializer.data
        assert "password_confirm" not in serializer.data
        assert user.check_password("StrongPassword123!")

    def test_username_is_required(self):
        """Username must be supplied."""
        data = self.valid_data()
        data.pop("username")

        serializer = UserRegistrationSerializer(data=data)

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_empty_username_is_rejected(self):
        """Whitespace-only usernames are rejected."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(username="   "),
        )

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_duplicate_username_is_rejected(self):
        """Duplicate usernames are rejected."""
        UserFactory(username="existing")

        serializer = UserRegistrationSerializer(
            data=self.valid_data(username="existing"),
        )

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_duplicate_username_is_case_insensitive(self):
        """Username uniqueness is case-insensitive."""
        UserFactory(username="ExistingUser")

        serializer = UserRegistrationSerializer(
            data=self.valid_data(username="existinguser"),
        )

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_duplicate_email_is_rejected(self):
        """Duplicate email addresses are rejected."""
        UserFactory(email="existing@example.com")

        serializer = UserRegistrationSerializer(
            data=self.valid_data(
                email="existing@example.com",
            ),
        )

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_duplicate_email_is_case_insensitive(self):
        """Email uniqueness is case-insensitive."""
        UserFactory(email="Existing@Example.com")

        serializer = UserRegistrationSerializer(
            data=self.valid_data(
                email="existing@example.com",
            ),
        )

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_email_can_be_blank(self):
        """Email is optional."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(email=""),
        )

        assert serializer.is_valid(), serializer.errors

    def test_password_confirmation_must_match(self):
        """Password confirmation must match the password."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(
                password_confirm="DifferentPassword123!",
            ),
        )

        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_weak_password_is_rejected(self):
        """Django password validation is applied."""
        serializer = UserRegistrationSerializer(
            data=self.valid_data(
                password="password",
                password_confirm="password",
            ),
        )

        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_client_cannot_assign_admin_role(self):
        """Registration does not expose role as a writable field."""
        data = self.valid_data(role=User.Role.ADMIN)

        serializer = UserRegistrationSerializer(data=data)

        assert "role" not in serializer.fields

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.role == User.Role.STUDENT


@pytest.mark.django_db
class TestLoginSerializer:
    """Tests for LoginSerializer."""

    def test_valid_credentials(self):
        """Valid credentials authenticate successfully."""
        UserFactory(
            username="john",
            password="StrongPassword123!",
        )

        serializer = LoginSerializer(
            data={
                "username": "john",
                "password": "StrongPassword123!",
            },
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"].username == "john"

    def test_invalid_password(self):
        """Invalid passwords are rejected."""
        UserFactory(
            username="john",
            password="StrongPassword123!",
        )

        serializer = LoginSerializer(
            data={
                "username": "john",
                "password": "WrongPassword123!",
            },
        )

        assert not serializer.is_valid()

    def test_missing_username(self):
        """Username is required."""
        serializer = LoginSerializer(
            data={
                "password": "StrongPassword123!",
            },
        )

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_missing_password(self):
        """Password is required."""
        serializer = LoginSerializer(
            data={
                "username": "john",
            },
        )

        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_inactive_user_cannot_login(self):
        """Inactive users cannot authenticate."""
        UserFactory(
            username="inactive",
            password="StrongPassword123!",
            is_active=False,
        )

        serializer = LoginSerializer(
            data={
                "username": "inactive",
                "password": "StrongPassword123!",
            },
        )

        assert not serializer.is_valid()


@pytest.mark.django_db
class TestPasswordChangeSerializer:
    """Tests for PasswordChangeSerializer."""

    def setUp(self):
        self.user = UserFactory(
            password="OldPassword123!",
        )

    def valid_data(self):
        return {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword456!",
            "password_confirm": "NewPassword456!",
        }

    def test_valid_password_change(self):
        """Valid password change data is accepted."""
        serializer = PasswordChangeSerializer(
            data=self.valid_data(),
            context={"user": self.user},
        )

        assert serializer.is_valid(), serializer.errors

    def test_wrong_current_password(self):
        """Incorrect current password is rejected."""
        data = self.valid_data()
        data["current_password"] = "WrongPassword123!"

        serializer = PasswordChangeSerializer(
            data=data,
            context={"user": self.user},
        )

        assert not serializer.is_valid()
        assert "current_password" in serializer.errors

    def test_new_passwords_must_match(self):
        """New password confirmation must match."""
        data = self.valid_data()
        data["password_confirm"] = "DifferentPassword456!"

        serializer = PasswordChangeSerializer(
            data=data,
            context={"user": self.user},
        )

        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_new_password_must_be_different(self):
        """The new password cannot equal the current password."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "OldPassword123!",
            "password_confirm": "OldPassword123!",
        }

        serializer = PasswordChangeSerializer(
            data=data,
            context={"user": self.user},
        )

        assert not serializer.is_valid()
        assert "new_password" in serializer.errors

    def test_user_is_required_in_context(self):
        """Authenticated user must be supplied in serializer context."""
        serializer = PasswordChangeSerializer(
            data=self.valid_data(),
        )

        assert not serializer.is_valid()
        assert "current_password" in serializer.errors


@pytest.mark.django_db
class TestUserUpdateSerializer:
    """Tests for UserUpdateSerializer."""

    def test_updates_profile(self):
        """Profile fields can be updated."""
        user = UserFactory(
            username="oldname",
            first_name="Old",
        )

        serializer = UserUpdateSerializer(
            instance=user,
            data={
                "username": "newname",
                "first_name": "New",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_user = serializer.save()

        assert updated_user.username == "newname"
        assert updated_user.first_name == "New"

    def test_duplicate_username_is_rejected(self):
        """An existing username cannot be claimed."""
        user = UserFactory(username="owner")
        UserFactory(username="existing")

        serializer = UserUpdateSerializer(
            instance=user,
            data={"username": "existing"},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_duplicate_email_is_rejected(self):
        """An existing email cannot be claimed."""
        user = UserFactory(email="owner@example.com")
        UserFactory(email="existing@example.com")

        serializer = UserUpdateSerializer(
            instance=user,
            data={"email": "existing@example.com"},
            partial=True,
        )

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_privileged_fields_are_not_writable(self):
        """Users cannot update privileged account fields."""
        user = UserFactory()

        serializer = UserUpdateSerializer(
            instance=user,
            data={
                "role": User.Role.ADMIN,
                "is_verified": True,
                "is_staff": True,
                "is_superuser": True,
            },
            partial=True,
        )

        assert "role" not in serializer.fields
        assert "is_verified" not in serializer.fields
        assert "is_staff" not in serializer.fields
        assert "is_superuser" not in serializer.fields


