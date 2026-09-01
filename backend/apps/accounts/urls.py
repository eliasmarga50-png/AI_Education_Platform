





"""
URL configuration for the accounts application.
"""

from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordChangeView,
    RegisterView,
    UserUpdateView,
)


app_name = "accounts"


urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
    path(
        "me/update/",
        UserUpdateView.as_view(),
        name="me-update",
    ),
    path(
        "password/change/",
        PasswordChangeView.as_view(),
        name="password-change",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
]


