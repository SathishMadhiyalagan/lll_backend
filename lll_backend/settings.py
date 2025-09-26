import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


ODBC_DRIVER = os.getenv('ODBC_DRIVER', '17')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-a6dzi=gb**yj=1fipqg))qgqzy%+pt84wr2%w^+)f8-twdk7su'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Configure allowed hosts based on the environment
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


INFO_LOGGING = os.getenv('INFO_LOGGING', 'False') == 'True'
WARNING_LOGGING = os.getenv('WARNING_LOGGING', 'False') == 'True'
ERROR_LOGGING = os.getenv('ERROR_LOGGING', 'False') == 'True'

INFO_PRINT = os.getenv('INFO_PRINT', 'False') == 'True'
WARNING_PRINT = os.getenv('WARNING_PRINT', 'False') == 'True'
ERROR_PRINT = os.getenv('ERROR_PRINT', 'False') == 'True'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
    "drf_yasg",  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lll_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lll_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database configuration
ODBC_DRIVER_V =  f'ODBC Driver {ODBC_DRIVER} for SQL Server' 

DATABASES = {
    'default': {
        'ENGINE': 'mssql',  # Use MS SQL database engine
        'NAME': os.getenv('DB_NAME'),  # Database name from .env
        'USER': os.getenv('DB_USER'),  # Database user from .env
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Database password from .env
        'HOST': os.getenv('DB_HOST'),  # Database host from .env
        'PORT': os.getenv('DB_PORT'),  # Database port from .env
        'OPTIONS': {
            'driver': ODBC_DRIVER_V,  # Choose the appropriate ODBC driver
            'autocommit': True,  # Enable autocommit for transactions
            'extra_params': 'DataTypeCompatibility=80;MARS Connection=True;',  # MS SQL options
            'use_legacy_date_fields': True,  # Legacy date fields support
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}



# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static file settings
STATIC_URL = '/static/'  # URL path for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Directory to store static files

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "JWT Authorization header using the Bearer scheme. Example: 'Bearer <token>'"
        }
    },
    'USE_SESSION_AUTH': False,
}

