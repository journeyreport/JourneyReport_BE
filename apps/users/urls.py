from django.urls import path
from django.conf.urls import url
from rest_framework import routers
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('auth/signin/', views.custom_obtain_auth_token, name='signin'),

]

router = routers.DefaultRouter()
router.register('auth', views.AuthViewSet, base_name='auth')
router.register('users', views.UsersViewSet, base_name='users')

urlpatterns += router.urls
