from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = "dev-secret-key-not-for-production"

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Разрешаем CORS для локального фронтенда на порту 3000
CORS_ALLOW_ALL_ORIGINS = True
