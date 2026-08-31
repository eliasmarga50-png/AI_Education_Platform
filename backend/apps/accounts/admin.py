



"""
Django admin configuration for the accounts application.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom User model."""

    list_display = (
        "username",
        "email",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Education Platform",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Education Platform",
            {
                "fields": (
                    "role",
                    "is_verified",
                ),
            },
        ),
    )

