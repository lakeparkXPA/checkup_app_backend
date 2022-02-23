
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from checkup_backend.settings import DEBUG

schema_view = get_schema_view(
    openapi.Info(
      title="DOCL Check Up",
      default_version='v1.2.0',
      description="DOCL Check up backend API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="hjshljy@docl.org"),
      license=openapi.License(name="BSD License"),
    ),
    url='https://testapi.docl.org/dev/django',
    public=DEBUG,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('patient/', include('patient.urls')),
    path('physician/', include('physician.urls'))
]
