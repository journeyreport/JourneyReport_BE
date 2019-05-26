from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls

from rest_framework.routers import DefaultRouter
router = DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/<version>/', include('apps.users.urls')),
]

urlpatterns += [
    url(r'^api/docs/', include_docs_urls(title='Journey Report API',
                                         authentication_classes=[],
                                         permission_classes=[])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
