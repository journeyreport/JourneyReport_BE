from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.storage_backends import delete_by_key


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(label=_("Email"), required=False)
    password = serializers.CharField(label=_("Password"), required=False, style={'input_type': 'password'})
    name = serializers.CharField(label=_("Name"), required=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not (email or password):
            raise serializers.ValidationError('Email and Password are required')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'email',
                  'first_name', 'last_name', 'picture',
                  'timezone', 'timezone_offset',)

    def get_picture(self, instance):
        if str(instance.picture).startswith('http'):
            return str(instance.picture)
        return self.context['request'].build_absolute_uri(instance.picture.url) if instance.picture else ""

    def create(self, validated_data):
        model = self.Meta.model
        user = model.objects.create(**validated_data)
        password = validated_data.pop('password')
        user.set_password(password)
        picture = self.context['request'].data.get('picture')
        if picture:
            if user.picture:
                delete_by_key(user.picture.name)
            user.picture = picture
        user.save()
        return user

    def update(self, instance, validated_data):
        picture = self.context['request'].data.get('picture')
        if picture:
            if instance.picture:
                delete_by_key(instance.picture.name)
            instance.picture = picture
        password = validated_data.pop('password') if 'password' in validated_data else None
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TimezoneDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('timezone', 'timezone_offset', )


class SignupUserSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'picture')
        extra_kwargs = {
            'email': {'required': True, 'allow_null': False},
            'password': {'required': True, 'allow_null': False},
            'first_name': {'allow_null': False},
            'last_name': {'allow_null': False},
            'picture': {'allow_null': False},
        }


class CheckEmailExistSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class FacebookLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
