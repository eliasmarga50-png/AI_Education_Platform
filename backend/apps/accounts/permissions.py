



"""
Custom permissions for the accounts application.

Permissions are responsible only for authorization decisions.
Business logic belongs in the service layer.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """
    Allow access only to authenticated, active users.

    DRF's IsAuthenticated checks authentication, while this permission
    additionally ensures that the account is active.
    """

    message = "You must be authenticated with an active account."

    def has_permission(self, request, view) -> bool:
        """Return True when the request user is authenticated and active."""
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
        )


class IsAdminUser(BasePermission):
    """Allow access only to users with the admin role."""

    message = "Admin access is required."

    def has_permission(self, request, view) -> bool:
        """Check whether the authenticated user has the admin role."""
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == user.Role.ADMIN
        )


class IsInstructorUser(BasePermission):
    """Allow access only to users with the instructor role."""

    message = "Instructor access is required."

    def has_permission(self, request, view) -> bool:
        """Check whether the authenticated user is an instructor."""
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == user.Role.INSTRUCTOR
        )


class IsStudentUser(BasePermission):
    """Allow access only to users with the student role."""

    message = "Student access is required."

    def has_permission(self, request, view) -> bool:
        """Check whether the authenticated user is a student."""
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == user.Role.STUDENT
        )


class IsVerifiedUser(BasePermission):
    """Allow access only to authenticated and verified users."""

    message = "Your account must be verified to perform this action."

    def has_permission(self, request, view) -> bool:
        """Check whether the authenticated user is verified."""
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_verified
        )


class IsAdminOrInstructor(BasePermission):
    """Allow access to administrators or instructors."""

    message = "Admin or instructor access is required."

    def has_permission(self, request, view) -> bool:
        """Check whether the user has an admin or instructor role."""
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        return user.role in (
            user.Role.ADMIN,
            user.Role.INSTRUCTOR,
        )


class IsAdminOrInstructorOrReadOnly(BasePermission):
    """
    Allow administrators and instructors full access.

    Unauthenticated users may perform safe/read-only requests.
    """

    message = "Admin or instructor access is required for this action."

    def has_permission(self, request, view) -> bool:
        """Allow safe methods publicly and write operations to staff roles."""
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        return user.role in (
            user.Role.ADMIN,
            user.Role.INSTRUCTOR,
        )


class IsOwner(BasePermission):
    """
    Allow users to access only their own object.

    The target object must expose a ``user`` attribute or be the
    authenticated user itself.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        """Check whether the object belongs to the authenticated user."""
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if obj is user:
            return True

        return getattr(obj, "user", None) == user


class IsOwnerOrAdmin(BasePermission):
    """
    Allow an object owner or administrator to access the object.
    """

    message = "You can only access your own resources."

    def has_object_permission(self, request, view, obj) -> bool:
        """Allow the owner or an administrator."""
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.role == user.Role.ADMIN:
            return True

        if obj is user:
            return True

        return getattr(obj, "user", None) == user
