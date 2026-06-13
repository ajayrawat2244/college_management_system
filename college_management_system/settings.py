# college_management_system/settings.py
"""
Final production-ready settings for the College Management System.
Multi-tenant | Session auth | DRF API | Full Django web layer.
"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def env(key, default=None, required=False):
    val = os.environ.get(key, default)
    if required and val is None:
        raise ImproperlyConfigured(f"Required env var '{key}' is not set.")
    return val


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY", "(p(2jimluj-2&l7v1wftln8k*u*8u%%egn7t4!=q-9@4dn+ce8)")
DEBUG      = env("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = env(
    "DJANGO_ALLOWED_HOSTS",
    ".lvh.me,.cms.localhost,localhost,127.0.0.1"
).split(",")

# ── Apps ──────────────────────────────────────────────────────
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
    "apps.web",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.platforms.middleware.TenantResolutionMiddleware",
    "apps.web.middleware.WebAuthRedirectMiddleware",
    "apps.audit.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "college_management_system.urls"

# ── Templates ──────────────────────────────────────────────────
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
                "apps.web.context_processors.tenant",
                "apps.web.context_processors.user_role",
                "apps.web.context_processors.subscription",
            ],
        },
    },
]

WSGI_APPLICATION = "college_management_system.wsgi.application"

# ── Database ───────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     env("DB_NAME",     "sms_db"),
        "USER":     env("DB_USER",     "ajay"),
        "PASSWORD": env("DB_PASSWORD", "mypassword"),
        "HOST":     env("DB_HOST",     "localhost"),
        "PORT":     env("DB_PORT",     "5432"),
        "CONN_MAX_AGE": 60,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth ───────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

LOGIN_URL          = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Sessions ───────────────────────────────────────────────────
SESSION_ENGINE          = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE      = 60 * 60 * 8
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE   = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE      = not DEBUG
CSRF_TRUSTED_ORIGINS    = env(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://*.lvh.me:8000,http://*.cms.localhost:8000",
).split(",")

# ── DRF ────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES":     ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.platforms.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "EXCEPTION_HANDLER": "apps.platforms.exceptions.custom_exception_handler",
    "NON_FIELD_ERRORS_KEY": "errors",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
}

# ── CORS ───────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS   = env("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True

# ── i18n / l10n ────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

# ── Static / Media ─────────────────────────────────────────────
STATIC_URL       = "/static/"
STATIC_ROOT      = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Storage ────────────────────────────────────────────────────
DEFAULT_FILE_STORAGE   = env("DEFAULT_FILE_STORAGE", "django.core.files.storage.FileSystemStorage")
AWS_ACCESS_KEY_ID      = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY  = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME     = env("AWS_S3_REGION_NAME", "ap-south-1")
AWS_DEFAULT_ACL        = "private"
AWS_S3_FILE_OVERWRITE  = False

# ── Multi-tenancy ──────────────────────────────────────────────
TENANT_SUBDOMAIN_SUFFIX = env("TENANT_SUBDOMAIN_SUFFIX", ".cms.localhost")
SUBSCRIPTION_CACHE_TTL  = 60 * 5

# ── Logging ────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django":             {"handlers": ["console"], "level": "INFO",    "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps":               {"handlers": ["console"], "level": "DEBUG",   "propagate": False},
    },
}

# ── Security (production) ──────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_PROXY_SSL_HEADER        = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    X_FRAME_OPTIONS                = "DENY"
