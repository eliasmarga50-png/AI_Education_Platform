



"""
Factories for the accounts application tests.
"""

import factory

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(
        lambda n: f"testuser{n}",
    )
    email = factory.LazyAttribute(
        lambda user: f"{user.username}@example.com",
    )
    first_name = "Test"
    last_name = "User"
    role = User.Role.STUDENT
    is_verified = False
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set a properly hashed password."""
        if not create:
            return

        password = extracted or "StrongPassword123!"
        self.set_password(password)
        self.save(update_fields=["password"])



