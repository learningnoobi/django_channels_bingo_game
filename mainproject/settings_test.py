"""Settings for the test suite: debug on, in-memory database and channel layer."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.pop("REDIS_URL", None)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from .settings import *  # noqa: E402,F401,F403

ALLOWED_HOSTS = ["testserver", "localhost"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405

# Optionally run the suite against a real Redis channel layer: TEST_REDIS_URL=redis://localhost:6379
if os.environ.get("TEST_REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [os.environ["TEST_REDIS_URL"]]},
        }
    }

if os.environ.get("TEST_DATABASE_URL"):
    DATABASES = {"default": __import__("dj_database_url").parse(os.environ["TEST_DATABASE_URL"])}
