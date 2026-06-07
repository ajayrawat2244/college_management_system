# config/settings.py
"""
Production-ready settings for the College Management System.
Multi-tenancy: Shared DB + Shared Schema (row-level isolation via college_id).
Auth: Session-based (Django sessions).
API: Django REST Framework.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def env(key, default=None, required=False):
    val = os.environ.get(key, default)
    if required and val is None:
        raise ImproperlyConfigured(f"Environment variable '{key}' is required but not set.")
    return val


BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = "(p(2jimluj-2&l7v1wftln8k*u*8u%%egn7t4!=q-9@4dn+ce8"
DEBUG = True
ALLOWED_HOSTS = [
    ".lvh.me",
    "localhost",
    "127.0.0.1",
]
# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
]

LOCAL_APPS = [
    "apps.platforms",
    "apps.accounts",
    "apps.academics",
    "apps.attendance",
    "apps.content",
    "apps.exams",
    "apps.finance",
    "apps.audit",
    "apps.web"
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # --- Custom: resolves the current college tenant from subdomain/header ---
    "apps.platforms.middleware.TenantResolutionMiddleware",
    # --- Custom: writes audit log entries automatically ---
    "apps.audit.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "college_management_system.urls"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "college_management_system.wsgi.application"
# ---------------------------------------------------------------------------
# Database — PostgreSQL only
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sms_db", #env("DB_NAME", required=True),
        "USER": "ajay", #env("DB_USER", required=True),
        "PASSWORD": "mypassword", #env("DB_PASSWORD", required=True),
        "HOST": "localhost", #env("DB_HOST", "localhost"),
        "PORT": "5432", #env("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Authentication & Sessions
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Session stored in DB for auditability; switch to cache-backed for performance
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 8           # 8 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG           # True in production (HTTPS)
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

CSRF_COOKIE_HTTPONLY = False                # Frontend JS needs to read the CSRF token
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:3000"
).split(",")

LOGIN_URL = "/api/auth/login/"
LOGIN_REDIRECT_URL = "/"

# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Session auth for browser clients; BasicAuthentication only in DEBUG
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # All endpoints require login by default; override per-view as needed
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.platforms.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "EXCEPTION_HANDLER": "apps.platforms.exceptions.custom_exception_handler",
    "NON_FIELD_ERRORS_KEY": "errors",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
}

# ---------------------------------------------------------------------------
# CORS (for a separate frontend, e.g. React on localhost:3000)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True   # Required for session cookies cross-origin

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media Files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# File Storage (default local; override with S3 in production)
# ---------------------------------------------------------------------------
DEFAULT_FILE_STORAGE = env(
    "DEFAULT_FILE_STORAGE",
    "django.core.files.storage.FileSystemStorage",
)

# AWS S3 (only used when DEFAULT_FILE_STORAGE is set to S3Boto3Storage)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "ap-south-1")
AWS_DEFAULT_ACL = "private"
AWS_S3_FILE_OVERWRITE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",   # Set to DEBUG locally to see SQL queries
            "propagate": False,
        },
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

# ---------------------------------------------------------------------------
# Multi-Tenancy: Tenant Resolution
# ---------------------------------------------------------------------------
# The TenantResolutionMiddleware reads the tenant from:
#   1. Subdomain:  college-code.yourdomain.com  (production)
#   2. HTTP Header: X-College-ID  (API clients / mobile apps)
# The resolved College object is attached to request.college
TENANT_SUBDOMAIN_SUFFIX = env("TENANT_SUBDOMAIN_SUFFIX", ".cms.localhost")

# ---------------------------------------------------------------------------
# Subscription / Feature Flags
# ---------------------------------------------------------------------------
# Cached in memory by the SubscriptionService; refreshed on each request for
# the active college. Override per-college in CollegeSettings.feature_overrides.
SUBSCRIPTION_CACHE_TTL = 60 * 5   # 5 minutes

# ---------------------------------------------------------------------------
# Security Headers (production)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = False  # Handled by the reverse proxy (e.g. Nginx) in production
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
