import json

import facebook
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import mixins, viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes

from apps.mixins import SerializersMixin
from apps.storage_backends import delete_by_key
from apps.users.exceptions import NotSquareImageException
from . import serializers
from rest_framework.authtoken.views import ObtainAuthToken
import logging

logger = logging.getLogger('api')
logger.setLevel(logging.DEBUG)

User = get_user_model()

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'reset_code'
    )
)


class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = serializers.CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = user.get_token()
        return Response({'token': token})


custom_obtain_auth_token = CustomObtainAuthToken.as_view()


class AuthViewSet(SerializersMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    signup:
    Creates new user's account and returns an access token.

    signout:
    --

    fb_auth:
    Authorization or registration via  Facebook

    fb_callback:
    Callback for Facebook login
    """
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializers = {
        'default': serializers.UserSerializer,
        'signup': serializers.SignupUserSerializer,
        'check_email': serializers.CheckEmailExistSerializer,
        'fb_login': serializers.FacebookLoginSerializer,
        'check_email': serializers.CheckEmailExistSerializer
    }
    parser_classes = (MultiPartParser, FormParser, JSONParser,)

    @action(methods=['post'], detail=False, permission_classes=(AllowAny,))
    def signup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.set_password(request.data.get('password'))
        data = self.get_serializer(user, serializer_name='default').data
        data.update({
            'token': user.get_token(),
        })
        return Response(data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False, permission_classes=(IsAuthenticated,))
    def signout(self, request, *args, **kwargs):
        Token.objects.get(user=request.user).delete()
        return Response()

    @action(methods=['get'], detail=False, permission_classes=(AllowAny,))
    def fb_auth(self, request, *args, **kwargs):
        permissions = ['public_profile', 'email']
        callback_uri = f"https://{settings.SITE_DOMAIN}{reverse('auth-fb-callback', kwargs={'version': 'v1'})}"
        state = {}
        auth_url = facebook.auth_url(
            settings.FACEBOOK_APP_ID,
            callback_uri,
            perms=permissions,
            state=json.dumps(state),
        )
        return redirect(auth_url)

    def _fb_get_me(self, access_token):
        graph = facebook.GraphAPI(access_token=access_token)
        me = graph.get_object('me', fields='first_name,last_name,email,picture.type(large)')
        return {
            'fb_id': me['id'],
            'email': me['email'],
            'first_name': me['first_name'],
            'last_name': me['last_name'],
            'picture': me.get('picture', {}).get('data', {}).get('url')
        }

    @action(methods=['get'], detail=False, permission_classes=(AllowAny,))
    def fb_callback(self, request, *args, **kwargs):
        code = request.query_params.get('code')
        callback_uri = f"https://{settings.SITE_DOMAIN}{reverse('auth-fb-callback', kwargs={'version': 'v1'})}"

        try:
            fb_info = facebook.GraphAPI().get_access_token_from_code(
                code, callback_uri, settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
        except facebook.GraphAPIError:
            fb_info = {}

        access_token = fb_info.get('access_token')
        if not access_token:
            return Response({'Could not get facebook access token'}, status=status.HTTP_400_BAD_REQUEST)

        user_data = self._fb_get_me(access_token)
        user, c = User.objects.get_or_create(email=user_data['email'], defaults=user_data)

        return render(request, 'auth/fb_callback_response.html', {
            'token': user.get_token(),
            'registered': c,
        })

    """
    FB Login algorithm
    1) find User by FB ID
    2) not found - find by email and update fb_id
    3) not found - create User
    """
    @action(methods=['post'], detail=False, permission_classes=(AllowAny,))
    def fb_login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = request.data.get('access_token')

        if not access_token:
            return Response({'Could not get facebook access token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            c = False
            user_data = self._fb_get_me(access_token)
            user = User.objects.filter(fb_id=user_data['fb_id']).first()
            if not user:
                user = User.objects.filter(email=user_data['email']).first()
                if not user:
                    user, c = User.objects.get_or_create(email=user_data['email'], defaults=user_data)
                else:
                    user.fb_id = user_data['fb_id']
                    user.save()

        except KeyError as e:
            logger.info(f'KeyError: {e}')
            return Response({'Not all scopes provided. Need re-request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.info(e)
            return Response({'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'token': user.get_token(),
            'registered': c,
        })

    @action(methods=['post'], detail=False, permission_classes=(AllowAny,))
    def fb_convert_access_token(self, request, *args, **kwargs):
        access_token = request.data.get('fb_token')

        user_data = self._fb_get_me(access_token)
        user, c = User.objects.get_or_create(email=user_data['email'], defaults=user_data)
        data = {
            'token': user.get_token(),
            'registered': c,
        }
        return Response(data)

    @action(methods=['post'], detail=False, permission_classes=(AllowAny,))
    def check_email(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            'exist': User.objects.filter(email=request.data.get('email')).exists()
        })


class UsersViewSet(SerializersMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """
    me:
    Returns current user's object.

    list:
    Returns a list of friends. There are user instances from your phone contact list,
    FB friends and invited by email friends.

    retrieve:
    Using this method, you can get any friend, you have relationships with. Also you can get yourself by id.
    If you try to get someone else, you get 404 error, even though he really exists.

    update:
    You can update yourself only. If you try to update someone else, you get the 404 error.
    """
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializers = {
        "default": serializers.UserSerializer,
        "me": serializers.UserSerializer,
        "my_timezone_data": serializers.TimezoneDataSerializer,
    }
    parser_classes = (MultiPartParser, FormParser, JSONParser,)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'retrieve':  # returns me and friends only
            pks = list(self.request.user.subscriptions.values_list('related_user_id', flat=True))
            pks.append(self.request.user.pk)
            return qs.filter(pk__in=pks)
        elif self.action == 'list':  # returns friends only
            return qs.filter(
                pk__in=self.request.user.subscriptions.values_list('related_user_id', flat=True)
            )
        # otherwise returns user self only
        return qs.filter(pk=self.request.user.pk)

    @action(methods=('get',), detail=False)
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data)

    @action(methods=('put',), detail=False)
    def my_timezone_data(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.timezone = serializer.data['timezone']
            user.timezone_offset = serializer.data['timezone_offset']
            user.save()
            return Response({'status': 'timezone data set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['patch', 'put'], detail=True)
    def upload_picture(self, request, pk=None, *args, **kwargs):
        files = list(request.data.values())
        if not files:
            raise ValidationError({'picture': 'picture is required field'})
        try:
            user = get_user_model().objects.get(pk=pk)
        except get_user_model().DoesNotExist:
            raise ValidationError({'detail': 'There are no user with id %s' % pk})
        if user.picture:
            delete_by_key(user.picture.name)
        user.picture = files[0]
        try:
            user.save()
        except NotSquareImageException:
            raise ValidationError({'picture': 'Bad picture'})
        user.refresh_from_db()
        return self.retrieve(request, pk=user.pk, *args, **kwargs)

