import os
import sys
import ctypes.util
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Detect GDAL library path based on platform and environment
GDAL_LIBRARY_PATH = ctypes.util.find_library('gdal')

if GDAL_LIBRARY_PATH is None:
    if sys.platform == 'win32':
        GDAL_LIBRARY_PATH = os.path.join(os.environ.get('CONDA_PREFIX', ''), 'Library', 'bin', 'gdal.dll')
    elif sys.platform == 'darwin':
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            GDAL_LIBRARY_PATH = os.path.join(conda_prefix, 'lib', 'libgdal.dylib')
        else:
            GDAL_LIBRARY_PATH = '/opt/homebrew/lib/libgdal.dylib'
    else:
        # Linux or other Unix systems
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix:
            GDAL_LIBRARY_PATH = os.path.join(conda_prefix, 'lib', 'libgdal.so')
        else:
            GDAL_LIBRARY_PATH = None  # Set custom path if needed

print("GDAL_LIBRARY_PATH:", GDAL_LIBRARY_PATH)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-h48t$2zs$&2_#$=mo*g@n-j14ri^=$wn9bgze*v)%t0oone6ik'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '192.168.1.164',
    '192.168.11.116',
    'localhost',
    '127.0.0.1',
    '192.168.254.29',
    '192.168.1.165',
    '192.168.240.138',
    '192.168.18.106',
    '192.168.0.163',
    '192.168.1.176',
    '192.168.1.181',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django.contrib.gis',
    'leaflet',  # For map rendering

    'users',
    'supplier',
    'customer',
    'driver',
    'items',
    'orders',
    'account',
]

AUTH_USER_MODEL = 'users.User'

# Leaflet settings
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (27.7172, 85.3240),  # Kathmandu by default
    'DEFAULT_ZOOM': 13,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'SCALE': 'both',
    'ATTRIBUTION_PREFIX': 'Developed by deliver_it',
}

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'deliver_it.urls'

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

WSGI_APPLICATION = 'deliver_it.wsgi.application'

# Database configuration using environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# Email settings

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('HOST_EMAIL')  # Your email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Your app password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Firebase Cloud Messaging settings

FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY')
