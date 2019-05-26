from .base import *

DB_URL = os.environ.get('DB_URL', 'postgres://postgres:jreportpass@jreportdb:5432/jreport')
DATABASES = {
    'default': dj_database_url.config(default=DB_URL)
}

ALLOWED_HOSTS = ['*']

