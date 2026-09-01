



"""
Serializers for the accounts application.

Serializers are responsible for API input validation and output
representation. Business operations are delegated to AccountService.
"""

from __future__ import annotations


from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .services import AccountService


class UserSerializer(serializers.ModelSerializer):
    """Serializer for safely representing user account information."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "role",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
        )


class UserRegistrationSerializer(serializers.Serializer):
    """Validate and create a new user account."""

    username = serializers.CharField(
        max_length=150,
        required=True,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
    )

    def validate_username(self, value: str) -> str:
        """Validate username uniqueness."""
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username must not be empty."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return value

    def validate_email(self, value: str | None) -> str | None:
        """Normalize and validate the optional email address."""
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value

    def validate_password(self, value: str) -> str:
        """Run Django's configured password validators."""
        validate_password(value)
        return value

    def validate(self, attrs: dict) -> dict:
        """Ensure both password fields contain the same value."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data: dict) -> User:
        """Create the account through AccountService."""
        validated_data.pop("password_confirm")

        return AccountService.create_user(
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """Validate login credentials and authenticate the user."""

    username = serializers.CharField(
        required=True,
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict) -> dict:
        """Authenticate the supplied credentials."""
        username = attrs["username"].strip()
        password = attrs["password"]

        user = AccountService.authenticate_user(
            username=username,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        attrs["user"] = user

        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Validate a user's password change request."""

    current_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        """Ensure the current password is correct."""
        user = self.context.get("user")

        if user is None:
            raise serializers.ValidationError(
                "Authenticated user is required."
            )

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate_new_password(self, value: str) -> str:
        """Apply Django's configured password validators."""
        validate_password(
            value,
            self.context.get("user"),
        )
        return value

    def validate(self, attrs: dict) -> dict:
        """Ensure the new password fields match."""
        if attrs["new_password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Passwords do not match."
                }
            )

        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "The new password must be different "
                        "from the current password."
                    )
                }
            )

        return attrs

    def save(self, **kwargs) -> User:
        """Change the user's password through AccountService."""
        user = self.context["user"]

        return AccountService.change_password(
            user=user,
            new_password=self.validated_data["new_password"],
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating the authenticated user's profile."""

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
        )

    def validate_username(self, value: str) -> str:
        """Ensure the new username is unique."""
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username must not be empty."
            )

        user = self.instance

        if User.objects.filter(
            username__iexact=value,
        ).exclude(
            pk=user.pk,
        ).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return value

    def validate_email(self, value: str) -> str:
        """Ensure the new email is unique when supplied."""
        value = value.strip()

        if not value:
            return ""

        user = self.instance

        if User.objects.filter(
            email__iexact=value,
        ).exclude(
            pk=user.pk,
        ).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )

        return value

    def update(self, instance: User, validated_data: dict) -> User:
        """Update the profile through AccountService."""
        return AccountService.update_user(
            user=instance,
            **validated_data,
        )

