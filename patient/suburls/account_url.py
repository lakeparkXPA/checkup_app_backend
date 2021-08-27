from django.urls import path, include
from patient.views import patient_register, patient_login, patient_email_check, patient_edit, token_refresh

urlpatterns = [
    path('register', patient_register, name='patient_register'),
    path('login', patient_login, name='patient_login'),
    path('check', patient_email_check, name='patient_email_check'),
    path('edit', patient_edit, name='patient_edit'),


    path('refresh', token_refresh, name='token_refresh'),
]