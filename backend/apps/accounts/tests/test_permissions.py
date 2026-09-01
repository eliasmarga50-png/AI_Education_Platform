



"""
Tests for accounts permissions.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.accounts.permissions import (
    IsAdminOrInstructor,
    IsAdminOrInstructorOrReadOnly,
    IsAdminUser,
    IsAuthenticatedUser,
    IsInstructorUser,
    IsOwner,
    IsOwnerOrAdmin,
    IsStudentUser,
    IsVerifiedUser,
)

from .factories import UserFactory


factory = APIRequestFactory()


def request_with_user(
    user,
    method="get",
):
    """Create a request with a specific user."""
    request = getattr(factory, method)("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestIsAuthenticatedUser:
    """Tests for IsAuthenticatedUser."""

    def test_authenticated_active_user_is_allowed(self):
        user = UserFactory(is_active=True)
        request = request_with_user(user)

        assert IsAuthenticatedUser().has_permission(
            request,
            None,
        )

    def test_anonymous_user_is_denied(self):
        request = request_with_user(AnonymousUser())

        assert not IsAuthenticatedUser().has_permission(
            request,
            None,
        )

    def test_inactive_user_is_denied(self):
        user = UserFactory(is_active=False)
        request = request_with_user(user)

        assert not IsAuthenticatedUser().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsAdminUser:
    """Tests for IsAdminUser."""

    def test_admin_is_allowed(self):
        user = UserFactory(role=User.Role.ADMIN)
        request = request_with_user(user)

        assert IsAdminUser().has_permission(
            request,
            None,
        )

    def test_student_is_denied(self):
        user = UserFactory(role=User.Role.STUDENT)
        request = request_with_user(user)

        assert not IsAdminUser().has_permission(
            request,
            None,
        )

    def test_instructor_is_denied(self):
        user = UserFactory(role=User.Role.INSTRUCTOR)
        request = request_with_user(user)

        assert not IsAdminUser().has_permission(
            request,
            None,
        )

    def test_inactive_admin_is_denied(self):
        user = UserFactory(
            role=User.Role.ADMIN,
            is_active=False,
        )
        request = request_with_user(user)

        assert not IsAdminUser().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsInstructorUser:
    """Tests for IsInstructorUser."""

    def test_instructor_is_allowed(self):
        user = UserFactory(role=User.Role.INSTRUCTOR)
        request = request_with_user(user)

        assert IsInstructorUser().has_permission(
            request,
            None,
        )

    def test_student_is_denied(self):
        user = UserFactory(role=User.Role.STUDENT)
        request = request_with_user(user)

        assert not IsInstructorUser().has_permission(
            request,
            None,
        )

    def test_admin_is_denied(self):
        user = UserFactory(role=User.Role.ADMIN)
        request = request_with_user(user)

        assert not IsInstructorUser().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsStudentUser:
    """Tests for IsStudentUser."""

    def test_student_is_allowed(self):
        user = UserFactory(role=User.Role.STUDENT)
        request = request_with_user(user)

        assert IsStudentUser().has_permission(
            request,
            None,
        )

    def test_instructor_is_denied(self):
        user = UserFactory(role=User.Role.INSTRUCTOR)
        request = request_with_user(user)

        assert not IsStudentUser().has_permission(
            request,
            None,
        )

    def test_admin_is_denied(self):
        user = UserFactory(role=User.Role.ADMIN)
        request = request_with_user(user)

        assert not IsStudentUser().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsVerifiedUser:
    """Tests for IsVerifiedUser."""

    def test_verified_user_is_allowed(self):
        user = UserFactory(is_verified=True)
        request = request_with_user(user)

        assert IsVerifiedUser().has_permission(
            request,
            None,
        )

    def test_unverified_user_is_denied(self):
        user = UserFactory(is_verified=False)
        request = request_with_user(user)

        assert not IsVerifiedUser().has_permission(
            request,
            None,
        )

    def test_inactive_verified_user_is_denied(self):
        user = UserFactory(
            is_verified=True,
            is_active=False,
        )
        request = request_with_user(user)

        assert not IsVerifiedUser().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsAdminOrInstructor:
    """Tests for IsAdminOrInstructor."""

    @pytest.mark.parametrize(
        "role",
        [
            User.Role.ADMIN,
            User.Role.INSTRUCTOR,
        ],
    )
    def test_admin_or_instructor_is_allowed(self, role):
        user = UserFactory(role=role)
        request = request_with_user(user)

        assert IsAdminOrInstructor().has_permission(
            request,
            None,
        )

    def test_student_is_denied(self):
        user = UserFactory(role=User.Role.STUDENT)
        request = request_with_user(user)

        assert not IsAdminOrInstructor().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsAdminOrInstructorOrReadOnly:
    """Tests for read-only role permissions."""

    @pytest.mark.parametrize(
        "method",
        ["get", "head", "options"],
    )
    def test_safe_methods_are_allowed(self, method):
        request = request_with_user(
            AnonymousUser(),
            method=method,
        )

        assert IsAdminOrInstructorOrReadOnly().has_permission(
            request,
            None,
        )

    def test_student_cannot_write(self):
        user = UserFactory(role=User.Role.STUDENT)
        request = request_with_user(
            user,
            method="post",
        )

        assert not IsAdminOrInstructorOrReadOnly().has_permission(
            request,
            None,
        )

    @pytest.mark.parametrize(
        "role",
        [
            User.Role.ADMIN,
            User.Role.INSTRUCTOR,
        ],
    )
    def test_admin_or_instructor_can_write(self, role):
        user = UserFactory(role=role)
        request = request_with_user(
            user,
            method="post",
        )

        assert IsAdminOrInstructorOrReadOnly().has_permission(
            request,
            None,
        )


@pytest.mark.django_db
class TestIsOwner:
    """Tests for IsOwner."""

    def test_user_can_access_themselves(self):
        user = UserFactory()
        request = request_with_user(user)

        assert IsOwner().has_object_permission(
            request,
            None,
            user,
        )

    def test_user_can_access_owned_object(self):
        user = UserFactory()
        owned_object = type("OwnedObject", (), {})()
        owned_object.user = user

        request = request_with_user(user)

        assert IsOwner().has_object_permission(
            request,
            None,
            owned_object,
        )

    def test_user_cannot_access_another_users_object(self):
        user = UserFactory()
        other_user = UserFactory()

        owned_object = type("OwnedObject", (), {})()
        owned_object.user = other_user

        request = request_with_user(user)

        assert not IsOwner().has_object_permission(
            request,
            None,
            owned_object,
        )


@pytest.mark.django_db
class TestIsOwnerOrAdmin:
    """Tests for IsOwnerOrAdmin."""

    def test_owner_is_allowed(self):
        user = UserFactory()

        owned_object = type("OwnedObject", (), {})()
        owned_object.user = user

        request = request_with_user(user)

        assert IsOwnerOrAdmin().has_object_permission(
            request,
            None,
            owned_object,
        )

    def test_other_user_is_denied(self):
        user = UserFactory()
        other_user = UserFactory()

        owned_object = type("OwnedObject", (), {})()
        owned_object.user = other_user

        request = request_with_user(user)

        assert not IsOwnerOrAdmin().has_object_permission(
            request,
            None,
            owned_object,
        )

    def test_admin_can_access_other_users_object(self):
        admin = UserFactory(role=User.Role.ADMIN)
        other_user = UserFactory()

        owned_object = type("OwnedObject", (), {})()
        owned_object.user = other_user

        request = request_with_user(admin)

        assert IsOwnerOrAdmin().has_object_permission(
            request,
            None,
            owned_object,
        )






