



"""
Service layer for the accounts application.

Business logic related to user account management belongs here.
Views, serializers, and API endpoints should delegate account operations
to this service layer instead of implementing business rules themselves.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction


User = get_user_model()


class AccountService:
    """Provide business operations for user accounts."""

    @staticmethod
    @transaction.atomic
    def create_user(
        *,
        username: str,
        password: str,
        email: str | None = None,
        role: str | None = None,
        **extra_fields: Any,
    ) -> User:
        """
        Create a new user account.

        Password hashing and user persistence are delegated to the
        custom UserManager.
        """
        if not username:
            raise ValueError("The username must be set.")

        if not password:
            raise ValueError("The password must be set.")

        if role is not None:
            extra_fields["role"] = role

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

    @staticmethod
    def authenticate_user(
        *,
        username: str,
        password: str,
    ) -> User | None:
        """
        Authenticate a user using username and password.

        Returns:
            The authenticated user when credentials are valid;
            otherwise None.
        """
        if not username or not password:
            return None

        return authenticate(
            username=username,
            password=password,
        )

    @staticmethod
    def get_user_by_id(
        *,
        user_id: int,
    ) -> User | None:
        """Return a user by primary key."""
        return User.objects.filter(pk=user_id).first()

    @staticmethod
    def get_user_by_username(
        *,
        username: str,
    ) -> User | None:
        """Return a user by username."""
        if not username:
            return None

        return User.objects.filter(username=username).first()

    @staticmethod
    def get_user_by_email(
        *,
        email: str,
    ) -> User | None:
        """Return a user by email address."""
        if not email:
            return None

        return User.objects.filter(email=email).first()

    @staticmethod
    @transaction.atomic
    def update_user(
        *,
        user: User,
        **fields: Any,
    ) -> User:
        """
        Update editable user fields.

        Password changes should use change_password() so the password
        is always hashed correctly.
        """
        if not fields:
            return user

        for field, value in fields.items():
            setattr(user, field, value)

        user.save(update_fields=list(fields.keys()))

        return user

    @staticmethod
    @transaction.atomic
    def change_password(
        *,
        user: User,
        new_password: str,
    ) -> User:
        """Change a user's password securely."""
        if not new_password:
            raise ValueError("The new password must be set.")

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return user

    @staticmethod
    @transaction.atomic
    def activate_user(
        *,
        user: User,
    ) -> User:
        """Activate a user account."""
        if user.is_active:
            return user

        user.is_active = True
        user.save(update_fields=["is_active"])

        return user

    @staticmethod
    @transaction.atomic
    def deactivate_user(
        *,
        user: User,
    ) -> User:
        """Deactivate a user account without deleting it."""
        if not user.is_active:
            return user

        user.is_active = False
        user.save(update_fields=["is_active"])

        return user

    @staticmethod
    @transaction.atomic
    def verify_user(
        *,
        user: User,
    ) -> User:
        """Mark a user's account as verified."""
        if user.is_verified:
            return user

        user.is_verified = True
        user.save(update_fields=["is_verified"])

        return user

    @staticmethod
    @transaction.atomic
    def unverify_user(
        *,
        user: User,
    ) -> User:
        """Mark a user's account as unverified."""
        if not user.is_verified:
            return user

        user.is_verified = False
        user.save(update_fields=["is_verified"])

        return user

