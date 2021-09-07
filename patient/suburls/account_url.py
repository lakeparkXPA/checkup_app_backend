from django.urls import path
from patient.views import patient_register, patient_login, patient_email_check, patient_edit, token_refresh, \
    patient_remove

urlpatterns = [
    path('register', patient_register, name='patient_register'),
    path('login', patient_login, name='patient_login'),
    path('check', patient_email_check, name='patient_email_check'),
    path('edit', patient_edit, name='patient_edit'),
    path('remove', patient_remove, name='patient_remove'),


    path('refresh', token_refresh, name='token_refresh'),
]