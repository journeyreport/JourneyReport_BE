import sys

import hashlib
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO

from PIL import Image
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from rest_framework.authtoken.models import Token

from apps.users.exceptions import NotSquareImageException
import logging

logger = logging.getLogger('api')
logger.setLevel(logging.DEBUG)


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_registered=True)

    def create_user(self, email, password=None, username=None):
        if not email:
            raise ValueError("User must have an email")

        user = self.model(email=email)
        user.set_password(password)
        user.username = username
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name=_('Email address'), max_length=255, unique=True)
    password = models.CharField(_('Password'), max_length=128)
    fb_id = models.CharField(_('FB id'), max_length=32, blank=True, null=True, unique=True)

    first_name = models.CharField(_('First name'), max_length=128, blank=True, null=True)
    last_name = models.CharField(_('Last name'), max_length=128, blank=True, null=True)
    picture = models.ImageField(upload_to='userpics', max_length=3000, blank=True, null=True)

    is_active = models.BooleanField(_('Active'), default=True)
    is_admin = models.BooleanField(_('Admin'), default=False)

    is_registered = models.BooleanField(_('Registered'), default=True)
    last_activity_date = models.DateField(blank=True, null=True)
    registration_date = models.DateField(auto_now_add=True)
    timezone = models.CharField(max_length=10, blank=True)
    timezone_offset = models.IntegerField(blank=True, null=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__picture_origin = self.picture

    def __str__(self):
        return f"{self.get_full_name() or 'noname'} ({self.email})"

    def get_file_name(self):
        m = hashlib.md5()
        m.update(f"{timezone.now()}{self.pk}{settings.USERPIC_SALT}".encode())
        return f"{m.hexdigest()}-large.jpg"

    def resize_picture(self):
        if str(self.picture).startswith('http'):
            return
        im = Image.open(self.picture)
        if im.width != im.height:
            raise NotSquareImageException
        output = BytesIO()
        im = im.resize((200, 200))
        im.save(output, format='JPEG', quality=100)
        output.seek(0)
        self.picture = InMemoryUploadedFile(output, 'ImageField', self.get_file_name(), 'image/jpeg',
                                            sys.getsizeof(output), None)

    def save(self, *args, **kwargs):
        if self.picture and self.picture != self.__picture_origin:
            self.resize_picture()
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}"

    def get_short_name(self) -> str:
        last_name = self.last_name[0] if self.last_name else ''
        return " ".join([self.first_name or '', last_name])

    def has_module_perms(self, app_label) -> bool:
        # TODO: Need to implement this logic
        return True

    @property
    def is_staff(self) -> bool:
        return self.is_admin

    @property
    def is_superuser(self) -> bool:
        return self.is_admin

    @property
    def is_facebook(self) -> bool:
        return bool(self.fb_id)

    @classmethod
    def normalize_username(cls, username) -> str:
        return str(username)

    def update_last_activity_date(self):
        previous = self.last_activity_date
        present = timezone.now().date()
        self.last_activity_date = present
        self.save()
        return previous, present

