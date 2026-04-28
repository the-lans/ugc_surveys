import tempfile

from .base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = "test-secret-key-that-is-long-enough-for-jwt-hmac-sha256"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Быстрый hasher: тесты не проверяют стойкость паролей, зато выполняются в разы быстрее
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MEDIA_ROOT = tempfile.mkdtemp()

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
