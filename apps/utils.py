import logging

from rest_framework.renderers import JSONRenderer


logger = logging.getLogger('errors')


class UTF8CharsetJSONRenderer(JSONRenderer):
    charset = 'utf-8'
