import raven

from .base import *


DEBUG = os.environ.get('DEBUG', False)
CURRENT_HOST = os.environ.get('CURRENT_HOST', '')
ALLOWED_HOSTS = [CURRENT_HOST]

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PATH = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
CELERY_BROKER_URL = REDIS_PATH
CELERY_RESULT_BACKEND = REDIS_PATH

CACHES['default']['LOCATION'] = [REDIS_PATH, ]

