from django.urls import path, include
from patient.views import set_fixed, set_daily

urlpatterns = [
    path('setDaily', set_daily, name='set_daily'),
    path('setFixed', set_fixed, name='set_fixed'),
]