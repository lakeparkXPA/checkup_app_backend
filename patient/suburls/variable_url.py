from django.urls import path, include
from patient.views import set_fixed, set_daily, Fixed

urlpatterns = [
    path('setDaily', set_daily, name='set_daily'),
    path('fixed', Fixed.as_view()),
]