# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import os
import socket
from pathlib import Path

logger = logging.getLogger(__name__)


def get_from_env(
    var_name: str, valid_values: list = None, allow_missing: bool = False, default_value: str = None
):
    value = os.environ.get(var_name)
    if value is None and not allow_missing:
        raise ValueError(f"Missing environment variable {var_name}")
    if valid_values is not None and value not in valid_values:
        raise ValueError(f"Invalid value for {var_name}: {value}")
    if value is None:
        return default_value
    return value


# Build paths inside the project like this: BASE_DIR / 'subdir'.
DB_DIR = Path(get_from_env("HAMILTON_BASE_DIR", allow_missing=True))
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
DEBUG = True

HAMILTON_ENV = "mini"

SECRET_KEY = "test_do_not_use_in_production"

HAMILTON_AUTH_MODE = "permissive"

# set up allowed hosts
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    hosts_to_add = [local_ip, hostname]
except Exception:
    logger.warning("Could not get hostname or local IP")
    hosts_to_add = []
ALLOWED_HOSTS = ["localhost", "backend", "0.0.0.0", "127.0.0.1", "colab.research.google.com"]
ALLOWED_HOSTS = (
    ALLOWED_HOSTS + hosts_to_add + os.environ.get("HAMILTON_ALLOWED_HOSTS", "").split(",")
)
logger.debug(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

HAMILTON_BLOB_STORE = "local"

HAMILTON_BLOB_STORE_PARAMS = {"base_dir": os.path.join(DB_DIR, "blobs")}

# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)

# ALLOWED_HOSTS = ALLOWED_HOSTS + [local_ip] + [hostname]

ADMIN_ENABLED = False

# Application definition

INSTALLED_APPS = [
    "trackingserver_base.apps.TrackingServerConfig",
    "trackingserver_auth.apps.TrackingServerAuthConfig",
    "trackingserver_projects.apps.TrackingServerProjectConfig",
    "trackingserver_template.apps.TrackingServerTemplateConfig",
    "trackingserver_run_tracking.apps.TrackingServerRunTracking",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
]

MIDDLEWARE = [
    "server.middleware.healthcheck.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "build")],
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
WSGI_APPLICATION = "server.wsgi.application"

# STATIC_ROOT = "./staticfiles"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "build/static/"),
]

# Add for serving the 'index.html' and other build files not in STATICFILES_DIRS
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "build/")
# WHITENOISE_ROOT = os.path.join(BASE_DIR, 'build')


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DB_DIR / "db.sqlite3"},
}
DB = DATABASES["default"]["ENGINE"]

app_names = [app.split(".")[0] for app in INSTALLED_APPS if app.startswith("trackingserver")]

MIGRATION_MODULES = {
    # app_name: f"{app.name.split('.')[0]}.migrations_sqlite" for app_name in INSTALLED_APPS if app.name.startswith("trackingserver")
    app_name: f"{app_name}.migrations_sqlite"
    for app_name in app_names
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST STUFF
REST_FRAMEWORK = {
    # your other DRF settings here
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "special": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s[%(asctime)s] %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "special",
            # "filters": ["truncate_sql"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # "django.db.backends": {
        #     "level": "DEBUG",
        #     "handlers": ["console"],
        #     "propagate": False,
        # },
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 100  # 250MB
SILKY_PYTHON_PROFILER = False
