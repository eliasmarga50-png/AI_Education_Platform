



"""
API views for the accounts application.

Views are intentionally kept thin. They coordinate HTTP requests,
serializers, permissions, and the account service layer.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAuthenticatedUser
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class RegisterView(APIView):
    """
    Register a new user account.

    Public endpoint.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Create a new user account."""
        serializer = UserRegistrationSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate a user and issue JWT access/refresh tokens.

    Public endpoint.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate credentials and return JWT tokens."""
        serializer = LoginSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    Return information about the currently authenticated user.
    """

    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        """Return the authenticated user's profile."""
        serializer = UserSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserUpdateView(APIView):
    """
    Update the authenticated user's profile.
    """

    permission_classes = [IsAuthenticatedUser]

    def patch(self, request):
        """Partially update the authenticated user's profile."""
        serializer = UserUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Profile updated successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(APIView):
    """
    Change the authenticated user's password.
    """

    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        """Validate and change the user's password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={
                "user": request.user,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Password changed successfully.",
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Blacklist a refresh token to log the user out.

    Requires the SimpleJWT blacklist application to be enabled.
    """

    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        """Blacklist the supplied refresh token."""
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError:
            return Response(
                {
                    "detail": "Invalid or expired refresh token.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Logout successful.",
            },
            status=status.HTTP_205_RESET_CONTENT,
        )
