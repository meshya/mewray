"""
Django settings for mewray project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('MEWRAY_DEBUG', 'true') == 'true'
DISABLE_CACHE = os.environ.get('MEWRAY_DISABLE_CACHE', 'false') == 'true'
DEBUG_PROXY = os.environ.get('DEBUG_PROXY', None)
REDIS_CONNECTION = os.environ.get('REDIS_CONNECTION', None)
USE_REDIS = True if REDIS_CONNECTION else False

if DEBUG:
    SECRET_KEY = 'django-insecure-&ygc++d&z0%e5q5lt2zy^uxf!215x@(7c0a7op=(c#9aaa6mb('
else:
    SECRET_KEY = os.environ.get('MEWRAY_SECRET_KEY', '')

HOST_NAME = os.environ.get('HOST_NAME', 'localhost')

ALLOWED_HOSTS = [
    HOST_NAME,
    "127.0.0.1",
    'localhost'
]

CSRF_TRUSTED_ORIGINS = [
    *[f'https://{h}' for h in ALLOWED_HOSTS],
    *[f'http://{h}' for h in ALLOWED_HOSTS]
]


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'repo',
    'api',
    'panel',
    'core',
    'sub',
    'apikey',
    'drf_spectacular',
    'drf_spectacular_sidecar'
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'EXCEPTION_HANDLER': 'api.views.AuthErrorHandler',
}

SPECTACULAR_SETTINGS = {
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'TITLE': 'Manager api',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'DESCRIPTION': '''
    ## Does it work?
    ''',
}

if USE_REDIS:
    CELERY_BROKER_URL = REDIS_CONNECTION
    CELERY_RESULT_BACKEND = REDIS_CONNECTION
else:
    CELERY_BROKER_URL = f"sqla+sqlite:////{BASE_DIR}/broker.sqlite3"
    CELERY_RESULT_BACKEND = f"db+sqlite:////{BASE_DIR}/results.sqlite"
CELERY_TASK_ALWAYS_EAGER = DEBUG
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

ASGI_APPLICATION = "mewray.asgi.application"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mewray.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mewray.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if DISABLE_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    if USE_REDIS:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": REDIS_CONNECTION
            }
        }
    else:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake",
            }
        }

CACHES['mem'] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "unique-snowflake",
}

STATIC_URL = '/static/' 'drf_spectacular',

if not True:
    # Static files (CSS, JavaScript, Images)
    # The directory where static files will be collected
    STATIC_ROOT = '/app/staticfiles/'  # Make sure this matches your Nginx config
else:
    STATIC_ROOT = BASE_DIR/'staticfiles'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
