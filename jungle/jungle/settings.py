"""
Django settings for jungle project.

Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from os import environ, path, getenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = path.join(BASE_DIR, 'media/')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ['djangosecret']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (getenv("djangodebug") == None)

ALLOWED_HOSTS = [
    "35.228.1.223",
    "127.0.0.1", 
    "localhost",
    "yanpan.fi", 
    "www.yanpan.fi",
    "yan.fi", 
    "www.yan.fi",
    "v2.yan.fi",
    "staging.yan.fi",
    "86.50.253.249",
]
X_FRAME_OPTIONS = 'SAMEORIGIN'


# Application definition
INSTALLED_APPS = [
    'play',
    'webreader',
    'ycrawl',
    'frontend',
    'vision',
    'yancv',
    'messenger',
    'rest_framework',
    'rest_framework.authtoken',
    'django_otp',
    'django_otp.plugins.otp_totp',
    # 'django_otp.plugins.otp_static',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jungle.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'jungle.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # for sqlite write lock timeout
        'OPTIONS': {
            'timeout': 15,
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'jungle.authentication.BearerAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',
        'rest_framework.renderers.JSONOpenAPIRenderer'
    ]
}

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Logging 
# https://docs.djangoproject.com/en/4.0/topics/logging/  

if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '{asctime} {name} {levelname} {message} | {module} {process:d} {thread:d} ',
                'style': '{',
            },
            'simple': {
                'format': '{asctime} {levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'logfile': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': "jungle.log",
                'maxBytes': int(1e6) ,
                'backupCount': 2,
                'formatter': 'verbose',
            },
            'baselogfile': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': "jungle-base.log",
                'maxBytes': int(1e6) ,
                'backupCount': 2,
                'formatter': 'verbose',
            },
            'console':{
                'level':'INFO',
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'loggers': {
            'dataprocessor': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'django': {
                'handlers': ['baselogfile'], #'console' not used in prod
                'propagate': True,
                'level':'INFO',
            },
            'django.db.backends': {
                'handlers': ['baselogfile'],
                'level': 'INFO',
                'propagate': False,
            },
            'frontend': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'messenger': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'webreader': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'vision': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'yancv': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
            'ycrawl': {
                'handlers': ['logfile'],
                'level': 'INFO',
            },
        }
    }
