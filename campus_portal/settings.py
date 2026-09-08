"""
Django settings for campus_portal project.
Campus Issue Portal - Production Ready Configuration
"""

import os
from pathlib import Path


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# Load .env if it exists locally.
# Render environment variables will take priority because
# os.environ.setdefault() does not overwrite existing variables.
env_file = BASE_DIR / ".env"

if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if (
                line
                and not line.startswith("#")
                and "=" in line
            ):
                key, val = line.split("=", 1)

                key = key.strip()
                val = val.strip().strip('"').strip("'")

                os.environ.setdefault(key, val)


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-campus-portal-development-key"
)

# IMPORTANT:
# Production should explicitly set DEBUG=False in Render.
DEBUG = os.getenv(
    "DEBUG",
    "False"
).lower() in ("true", "1", "yes")


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

# Required for HTTPS POST requests when deployed on Render.
#
# Render environment variable example:
#
# CSRF_TRUSTED_ORIGINS=https://campus-issue-portal.onrender.com
#

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    # Django built-in applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Campus Issue Portal
    "portal.apps.PortalConfig",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    # Security
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves static files in production
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # Sessions
    "django.contrib.sessions.middleware.SessionMiddleware",

    # Common HTTP functionality
    "django.middleware.common.CommonMiddleware",

    # CSRF protection
    "django.middleware.csrf.CsrfViewMiddleware",

    # Authentication
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Messages
    "django.contrib.messages.middleware.MessageMiddleware",

    # Clickjacking protection
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Campus Issue Portal custom authentication
    "portal.middleware.MongoAuthMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "campus_portal.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "portal" / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

                "django.template.context_processors.media",

                "portal.context_processors.portal_context",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "campus_portal.wsgi.application"


# ============================================================
# DJANGO DATABASE
# ============================================================

# The portal's main application data is stored in MongoDB.
#
# SQLite remains configured because Django's built-in
# applications may require a relational database for things
# such as sessions/admin migrations.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# MONGODB
# ============================================================

# LOCAL DEVELOPMENT:
#
# MONGO_URI=mongodb://localhost:27017/
#
# PRODUCTION / RENDER:
#
# MONGO_URI=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/
#
# The Render environment variable overrides this fallback.

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "campus_issue_portal"
)


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {
            "min_length": 6,
        },
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

# Browser URL:
# /static/

STATIC_URL = "/static/"


# Development static source directory:
#
# portal/
# └── static/
#     ├── css/
#     ├── js/
#     └── images/

STATICFILES_DIRS = [
    BASE_DIR / "portal" / "static",
]


# Production collected static files:
#
# python manage.py collectstatic --noinput
#
# will collect everything into this directory.

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# WHITENOISE STATIC FILE STORAGE
# ============================================================

# WhiteNoise allows Gunicorn/Render to serve Django static files
# without requiring a separate Nginx server.

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage."
            "FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ============================================================
# MEDIA FILES
# ============================================================

# Used for issue attachments/evidence.

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# Maximum upload size: 5 MB

MAX_UPLOAD_SIZE = 5 * 1024 * 1024


# Allowed upload extensions

ALLOWED_UPLOAD_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".webp",
    ".doc",
    ".docx",
]


# ============================================================
# SESSION SECURITY
# ============================================================

# Session lifetime: 7 days

SESSION_COOKIE_AGE = 86400 * 7

# Prevent JavaScript from reading the session cookie.

SESSION_COOKIE_HTTPONLY = True

# Save session on every request.

SESSION_SAVE_EVERY_REQUEST = True


# ============================================================
# PRODUCTION HTTPS SECURITY
# ============================================================

# Render sits behind a proxy/load balancer.
# This tells Django that the original request was HTTPS.

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Only enable secure cookies when running in production.
#
# This keeps local HTTP development working.

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# SameSite protection.

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# SECURITY HEADERS
# ============================================================

# Tell browsers to prefer HTTPS in production.

SECURE_SSL_REDIRECT = not DEBUG


# Prevent MIME-type sniffing.

SECURE_CONTENT_TYPE_NOSNIFF = True


# Clickjacking protection.

X_FRAME_OPTIONS = "DENY"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
