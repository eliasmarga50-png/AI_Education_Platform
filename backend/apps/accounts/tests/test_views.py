



"""
Integration tests for accounts API views.
"""

import pytest
from django.urls import include, path, reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


urlpatterns = [
    path(
        "api/v1/accounts/",
        include("apps.accounts.urls"),
    ),
]


@pytest.mark.django_db
class TestRegisterView(APITestCase):
    """Tests for user registration."""

    def test_register_user(self):
        """A valid registration request creates a user."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newstudent",
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": "New",
                "last_name": "Student",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["message"] == (
            "Account created successfully."
        )
        assert response.data["user"]["username"] == "newstudent"

        user = User.objects.get(username="newstudent")

        assert user.email == "student@example.com"
        assert user.role == User.Role.STUDENT
        assert user.check_password("StrongPassword123!")

    def test_registration_rejects_duplicate_username(self):
        """Duplicate usernames return validation errors."""
        User.objects.create_user(
            username="existing",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "existing",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "username" in response.data

    def test_registration_rejects_mismatched_passwords(self):
        """Mismatched passwords are rejected."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student",
                "password": "StrongPassword123!",
                "password_confirm": "DifferentPassword123!",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "password_confirm" in response.data

    def test_registration_cannot_assign_admin_role(self):
        """A client cannot promote itself during registration."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "role": User.Role.ADMIN,
            },
            format="json",
        )

        assert response.status_code == 201

        user = User.objects.get(username="student")

        assert user.role == User.Role.STUDENT


@pytest.mark.django_db
class TestLoginView(APITestCase):
    """Tests for login."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            password="StrongPassword123!",
        )

    def test_login_returns_jwt_tokens(self):
        """Valid credentials return access and refresh tokens."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "john",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["message"] == "Login successful."
        assert response.data["user"]["username"] == "john"
        assert response.data["access"]
        assert response.data["refresh"]

    def test_login_rejects_invalid_password(self):
        """Invalid credentials return a validation error."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "john",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_login_rejects_unknown_user(self):
        """Unknown users cannot authenticate."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "does-not-exist",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_inactive_user_cannot_login(self):
        """Inactive accounts cannot log in."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "john",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestMeView(APITestCase):
    """Tests for the current-user endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="StrongPassword123!",
        )

    def test_authenticated_user_can_view_profile(self):
        """Authenticated users can retrieve their profile."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("accounts:me"),
        )

        assert response.status_code == 200
        assert response.data["username"] == "john"
        assert response.data["email"] == "john@example.com"

    def test_unauthenticated_user_is_denied(self):
        """Unauthenticated users cannot access the profile."""
        response = self.client.get(
            reverse("accounts:me"),
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestUserUpdateView(APITestCase):
    """Tests for profile updates."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="StrongPassword123!",
        )

        self.client.force_authenticate(user=self.user)

    def test_update_profile(self):
        """Authenticated users can update their profile."""
        response = self.client.patch(
            reverse("accounts:me-update"),
            {
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["message"] == (
            "Profile updated successfully."
        )
        assert response.data["user"]["first_name"] == "John"
        assert response.data["user"]["last_name"] == "Doe"

    def test_user_cannot_change_role(self):
        """Users cannot change their own role."""
        response = self.client.patch(
            reverse("accounts:me-update"),
            {
                "role": User.Role.ADMIN,
            },
            format="json",
        )

        assert response.status_code == 200

        self.user.refresh_from_db()

        assert self.user.role == User.Role.STUDENT

    def test_user_cannot_change_staff_status(self):
        """Users cannot make themselves staff."""
        response = self.client.patch(
            reverse("accounts:me-update"),
            {
                "is_staff": True,
            },
            format="json",
        )

        assert response.status_code == 200

        self.user.refresh_from_db()

        assert self.user.is_staff is False


@pytest.mark.django_db
class TestPasswordChangeView(APITestCase):
    """Tests for password changes."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            password="OldPassword123!",
        )

        self.client.force_authenticate(user=self.user)

    def test_change_password(self):
        """Authenticated users can change their password."""
        response = self.client.post(
            reverse("accounts:password-change"),
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "password_confirm": "NewPassword456!",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["message"] == (
            "Password changed successfully."
        )

        self.user.refresh_from_db()

        assert self.user.check_password("NewPassword456!")
        assert not self.user.check_password("OldPassword123!")

    def test_wrong_current_password_is_rejected(self):
        """Incorrect current passwords are rejected."""
        response = self.client.post(
            reverse("accounts:password-change"),
            {
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
                "password_confirm": "NewPassword456!",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_unauthenticated_user_is_denied(self):
        """Unauthenticated users cannot change passwords."""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("accounts:password-change"),
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "password_confirm": "NewPassword456!",
            },
            format="json",
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestLogoutView(APITestCase):
    """Tests for logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            password="StrongPassword123!",
        )

        self.client.force_authenticate(user=self.user)

    def test_logout_requires_refresh_token(self):
        """Logout requires a refresh token."""
        response = self.client.post(
            reverse("accounts:logout"),
            {},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["detail"] == (
            "Refresh token is required."
        )

    def test_logout_rejects_invalid_refresh_token(self):
        """Invalid refresh tokens are rejected."""
        response = self.client.post(
            reverse("accounts:logout"),
            {
                "refresh": "invalid-token",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_logout_blacklists_refresh_token(self):
        """
        A valid refresh token is blacklisted during logout.

        This test requires rest_framework_simplejwt.token_blacklist
        to be installed and configured.
        """
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            reverse("accounts:logout"),
            {
                "refresh": str(refresh),
            },
            format="json",
        )

        assert response.status_code == 205
        assert response.data["message"] == "Logout successful."






