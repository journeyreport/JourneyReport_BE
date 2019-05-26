from datetime import time, datetime, date
from decimal import Decimal

from django.apps import apps
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


class SerializersMixin(object):
    serializers = {}
    serializer_class = None
    default_name = 'default'
    _serializers = {
        default_name: serializer_class,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.serializer_class and not self.serializers.get(self.default_name):
            raise ValueError("Need to specify either 'serializer_class' or 'serializers default' class")
        self._serializers.update(self.serializers)

    def get_serializer_class(self, serializer_name=None):
        return self.serializers.get(serializer_name) \
               or self.serializers.get(self.action) \
               or self.serializers.get(self.default_name) \
               or super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class(serializer_name=kwargs.pop('serializer_name', None))
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class ModelMixin(APITestCase):
    base_name = None
    response = None
    format = 'json'
    model = None
    _model = None

    def __init__(self, *args, **kwargs):
        super(ModelMixin, self).__init__(*args, **kwargs)
        if self.model:
            self._model = apps.get_model(self.model)

    def setUp(self):
        self.client = APIClient()

    def __get_response_data(self, response=None):
        data = response.data if response else self.response.data
        if isinstance(data, dict):
            for key in ['page', 'results']:  # 'data' maybe needed
                try:
                    data = data[key]
                except KeyError:
                    pass
                except TypeError:
                    pass
        return data

    def __get_view_path(self, pk=None, *args, **kwargs):
        path = kwargs.get('path')
        urlname = kwargs.get('urlname')
        path_key = kwargs.get('key')

        if path:
            return path

        reverse_kwargs = {}
        if pk and isinstance(pk, int):
            reverse_kwargs.update({path_key: pk})
        if pk and isinstance(pk, Model):
            reverse_kwargs.update({path_key: pk.pk})

        if urlname:
            return reverse(urlname, kwargs=reverse_kwargs)
        return reverse(self.base_name, kwargs=reverse_kwargs)

    def __request(self, method, obj=None, *args, **kwargs):
        headers = kwargs.pop('headers', self.get_headers())
        path_key = kwargs.pop('key', 'pk')
        path = self.__get_view_path(pk=obj, key=path_key, *args, **kwargs)
        path = kwargs.pop('path', path)
        data = kwargs.pop('data', None)
        self.response = method(
            path=path,
            headers=headers,
            format=self.get_format(),
            data=data,
        )
        return self.response

    @property
    def data(self):
        return self.__get_response_data()

    @property
    def model_objects(self):
        if self._model:
            return self._model.objects
        raise ValueError("model attribute must be filled")

    def assertFields(self, response, obj, fields, null=True):
        if isinstance(response, dict):
            data = response
        else:
            data = self.__get_response_data(response)

        for field in fields:
            obj_field = getattr(obj, field)
            if not null:
                self.assertIsNotNone(obj_field)
                self.assertIsNotNone(data.get(field))
            if isinstance(obj_field, Model):
                self.assertEqual(data.get(field), obj_field.pk)
            elif isinstance(obj_field, time):
                try:
                    response_field_value = datetime.strptime(data.get(field), '%H:%M:%S.%f').time()
                except ValueError:
                    response_field_value = datetime.strptime(data.get(field), '%H:%M:%S').time()
                self.assertEqual(response_field_value, obj_field)
            elif isinstance(obj_field, date):
                self.assertEqual(datetime.strptime(data.get(field), '%Y-%m-%d').date(), obj_field)
            elif isinstance(obj_field, Decimal):
                self.assertEqual(Decimal(data.get(field)), obj_field)
            elif isinstance(obj_field, FieldFile):
                pass
                # TODO: Need to implement this part
            else:
                self.assertEqual(data.get(field), obj_field)

    def assertFieldsDict(self, obj, data, fields=None):
        for k, v in data.items():
            if fields and k in fields:
                self.assertEqual(getattr(obj, k), v)

    def assertFieldError(self, response, field, msg=None):
        if msg:
            self.assertEqual(str(response.data.get(field, ['<No data>'])[0]), msg)
        self.assertIn(field, response.data)

    def assertNonFieldError(self, response, msg):
        if msg:
            self.assertEqual(str(response.data.get('non_field_errors', ['<No data>'])[0]), msg)
        self.assertIn('non_field_errors', response.data)

    def get_url(self, action, *args, **kwargs):
        if action in ('list', 'create',):
            route = 'list'
        elif action in ('retrieve', 'update', 'partial_update', 'delete'):
            route = 'detail'
        return reverse("{}-{}".format(self.base_name, route), *args, **kwargs)

    def get_headers(self):
        return {}

    def get_format(self):
        return self.format

    def login(self, user):
        self.client.force_authenticate(user=user)

    def logout(self):
        self.client.force_authenticate(user=None)

    def get(self, obj=None, *args, **kwargs):
        return self.__request(self.client.get, obj=obj, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.__request(self.client.post, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.__request(self.client.put, *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.__request(self.client.patch, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.__request(self.client.delete, *args, **kwargs)

    def list(self, *args, **kwargs):
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.get(
            reverse("{}-list".format(self.base_name)),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def retrieve(self, pk=None, *args, **kwargs):
        if not isinstance(pk, int):
            pk = pk.pk
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.get(
            reverse("{}-detail".format(self.base_name), kwargs={'pk': pk}),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def create(self, *args, **kwargs):
        headers = kwargs.pop('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.post(
            reverse("{}-list".format(self.base_name)),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def update(self, pk=None, *args, **kwargs):
        if not isinstance(pk, int):
            pk = pk.pk
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.put(
            reverse("{}-detail".format(self.base_name), kwargs={'pk': pk}),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def partial_update(self, pk=None, *args, **kwargs):
        if not isinstance(pk, int):
            pk = pk.pk
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.patch(
            reverse("{}-detail".format(self.base_name), kwargs={'pk': pk}),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def destroy(self, pk=None, *args, **kwargs):
        if not isinstance(pk, int):
            pk = pk.pk
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        self.response = self.client.delete(
            reverse("{}-detail".format(self.base_name), kwargs={'pk': pk}),
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response

    def action(self, name, pk=None, method='get', data=None, *args, **kwargs):
        headers = kwargs.get('headers', self.get_headers())
        request_format = kwargs.pop('format', self.get_format())
        if not data:
            data = {}
        kw = dict()
        if pk:
            if not isinstance(pk, int):
                pk = pk.pk
            kw.update({'pk': pk})
        self.response = getattr(self.client, method)(
            reverse("{}-{}".format(self.base_name, name), kwargs=kw),
            data=data,
            headers=headers,
            format=request_format,
            *args, **kwargs
        )
        return self.response


class StatusMixin(APITestCase):
    def assertStatus100(self, response):
        self.assertEqual(response.status_code, status.HTTP_100_CONTINUE)

    def assertStatus101(self, response):
        self.assertEqual(response.status_code, status.HTTP_101_SWITCHING_PROTOCOLS)

    def assertStatus200(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def assertStatus201(self, response):
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def assertStatus202(self, response):
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def assertStatus203(self, response):
        self.assertEqual(response.status_code, status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def assertStatus204(self, response):
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def assertStatus205(self, response):
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def assertStatus206(self, response):
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)

    def assertStatus207(self, response):
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)

    def assertStatus300(self, response):
        self.assertEqual(response.status_code, status.HTTP_300_MULTIPLE_CHOICES)

    def assertStatus301(self, response):
        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)

    def assertStatus302(self, response):
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def assertStatus303(self, response):
        self.assertEqual(response.status_code, status.HTTP_303_SEE_OTHER)

    def assertStatus304(self, response):
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def assertStatus305(self, response):
        self.assertEqual(response.status_code, status.HTTP_305_USE_PROXY)

    def assertStatus306(self, response):
        self.assertEqual(response.status_code, status.HTTP_306_RESERVED)

    def assertStatus307(self, response):
        self.assertEqual(response.status_code, status.HTTP_307_TEMPORARY_REDIRECT)

    def assertStatus400(self, response):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def assertStatus401(self, response):
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def assertStatus402(self, response):
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)

    def assertStatus403(self, response):
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def assertStatus404(self, response):
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def assertStatus405(self, response):
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def assertStatus406(self, response):
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def assertStatus407(self, response):
        self.assertEqual(response.status_code, status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED)

    def assertStatus408(self, response):
        self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)

    def assertStatus409(self, response):
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def assertStatus410(self, response):
        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    def assertStatus411(self, response):
        self.assertEqual(response.status_code, status.HTTP_411_LENGTH_REQUIRED)

    def assertStatus412(self, response):
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

    def assertStatus413(self, response):
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def assertStatus414(self, response):
        self.assertEqual(response.status_code, status.HTTP_414_REQUEST_URI_TOO_LONG)

    def assertStatus415(self, response):
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def assertStatus416(self, response):
        self.assertEqual(response.status_code, status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)

    def assertStatus417(self, response):
        self.assertEqual(response.status_code, status.HTTP_417_EXPECTATION_FAILED)

    def assertStatus422(self, response):
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def assertStatus423(self, response):
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

    def assertStatus424(self, response):
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    def assertStatus428(self, response):
        self.assertEqual(response.status_code, status.HTTP_428_PRECONDITION_REQUIRED)

    def assertStatus429(self, response):
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def assertStatus431(self, response):
        self.assertEqual(response.status_code, status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE)

    def assertStatus451(self, response):
        self.assertEqual(response.status_code, status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

    def assertStatus500(self, response):
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def assertStatus501(self, response):
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def assertStatus502(self, response):
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def assertStatus503(self, response):
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def assertStatus504(self, response):
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)

    def assertStatus505(self, response):
        self.assertEqual(response.status_code, status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED)

    def assertStatus507(self, response):
        self.assertEqual(response.status_code, status.HTTP_507_INSUFFICIENT_STORAGE)

    def assertStatus511(self, response):
        self.assertEqual(response.status_code, status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED)

    def assertStatusInformational(self, response):
        self.assertTrue(status.is_informational(response.status_code))

    def assertStatusSuccess(self, response):
        self.assertTrue(status.is_success(response.status_code))

    def assertStatusRedirect(self, response):
        self.assertTrue(status.is_redirect(response.status_code))

    def assertStatusClientError(self, response):
        self.assertTrue(status.is_client_error(response.status_code))

    def assertStatusServerError(self, response):
        self.assertTrue(status.is_server_error(response.status_code))


class TestWrapper(StatusMixin, ModelMixin, APITestCase):
    pass
