"""
Pytest configuration and shared fixtures for the Django application.
This file sets up common test fixtures and configurations.
"""

import os
import django
from django.conf import settings
import pytest


def pytest_configure(config):
    """Configure Django settings for pytest."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "be.settings")
    django.setup()


@pytest.fixture(scope="session")
def django_db_setup():
    """Set up test database."""
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
    }


@pytest.fixture
def api_client():
    """Provide Django REST framework API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_user(django_user_model):
    """Create an authenticated user for testing."""
    user = django_user_model.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    return user


@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    """Provide API client with authenticated user."""
    api_client.force_authenticate(user=authenticated_user)
    return api_client


@pytest.fixture
def admin_user(django_user_model):
    """Create an admin user for testing."""
    user = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )
    return user


@pytest.fixture
def admin_client(api_client, admin_user):
    """Provide API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests.
    This fixture is automatically used for all tests.
    """
    pass


@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "user_data": {
            "username": "sampleuser",
            "email": "sample@example.com",
            "password": "samplepass123",
            "first_name": "Sample",
            "last_name": "User",
        },
        "api_data": {
            "test_field": "test_value",
            "numeric_field": 42,
            "boolean_field": True,
        },
    }


@pytest.fixture
def mock_settings():
    """Provide mock Django settings for testing."""
    from django.test import override_settings

    return override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
    )


# Pytest markers for organizing tests
pytest_plugins = [
    "django.test.utils",
]

# Configure test discovery patterns
collect_ignore = [
    "migrations",
    "static",
    "media",
    "venv",
    ".venv",
]
