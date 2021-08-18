from django.urls import path, include
from patient.views import patient_register

urlpatterns = [
    path('register', patient_register, name='patient_register'),
    # path('login', patient_login, name='patient_login'),
]