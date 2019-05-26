from datetime import timedelta
from boto3.session import Session
import os
import dj_database_url

SITE_DOMAIN = ''
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTH_USER_MODEL = 'users.User'

SECRET_KEY = 'Jc-E@ONsxSA5RQRf4hCxm$DC8kI_I_^nWx_K0Q(OcjT%hr@EfUC'

API_VERSION = 'v1'

DEBUG = os.environ.get('DEBUG', True)
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')  # dev / stage / prod
IS_PROD = ENVIRONMENT == 'prod'
HOSTNAME = os.environ.get('HOSTNAME', 'localhost')  # ip-172-31-26-50
SEND_NOTIFICATIONS = os.environ.get('SEND_NOTIFICATIONS', False)

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'storages',
    'solo',
    'safedelete',

    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'rest_auth',

    'apps.users',
]

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

ROOT_URLCONF = 'config.urls'

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
    '127.0.0.1:5000',
    'localhost:5000',
    'localhost:8081',
)
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'

DB_URL = os.environ.get('DB_URL', '')
DATABASES = {
    'default': dj_database_url.config(default=DB_URL)
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
USERPIC_SALT = "vqhlho2lc09fvmfo14gcivvtohr8ujgn"

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'mysite/static'),
# ]

AWS_DEFAULT_ACL = 'public-read'
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_STORAGE_BUCKET_NAME = ''
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_REGION_NAME = 'us-west-1'

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

AWS_LOCATION = 'static'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

##### REST FRAMEWORK #####

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'apps.utils.UTF8CharsetJSONRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
}

##### REDIS SETTINGS #####

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

REDIS_PATH = f'redis://{REDIS_HOST}:{REDIS_PORT}/2'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': [REDIS_PATH, ],
        'TIMEOUT': 10,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.HerdClient',
        }
    },
}

##### CELERY SETTINGS #####

CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = REDIS_PATH
CELERY_RESULT_BACKEND = REDIS_PATH
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

##### LOGGING #####
AWS_LOGS_ACCESS_KEY_ID = 'AKIA2IQR2CHFFUVKB2UI'
AWS_LOGS_SECRET_ACCESS_KEY = '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'
boto3_session = Session(aws_access_key_id=AWS_LOGS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_LOGS_SECRET_ACCESS_KEY,
                        region_name=AWS_REGION_NAME)

# LOGS_PATH = os.path.join(BASE_DIR, 'logs')
LOGS_PATH = os.environ.get('LOGS_PATH', os.path.join(BASE_DIR, 'logs'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'aws': {
            # you can add specific format for aws here
            'format': u"%(asctime)s [%(levelname)-8s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'errors.log'),
            'formatter': 'standard',
        },
        'api': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'api.log'),
            'formatter': 'standard',
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_PATH, 'celery.log'),
            'formatter': 'standard',
        },
        'watchtower': {
            'level': 'DEBUG',
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_session': boto3_session,
            'log_group': '/jreport/logs',
            'stream_name': f'{ENVIRONMENT}-{HOSTNAME}',
            'formatter': 'aws',
        },
        'slack': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'config.helpers.slack_logger.SlackExceptionHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['slack'],
            'level': 'ERROR',
            'propagate': True,
        },
        'errors': {
            'handlers': ['errors'],
            'level': 'ERROR',
            'propagate': True,
        },
        'api': {
            'handlers': ['api', 'console', 'watchtower'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'celery': {
            'handlers': ['celery', 'watchtower'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

##### EMAILS
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'info@jreport.com'
CONTACT_US_EMAIL = 'info@jreport.com'

