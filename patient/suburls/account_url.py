from django.urls import path
from patient.views import patient_register, patient_login, patient_email_check, patient_edit, token_refresh, \
    patient_remove, patient_password_forget, patient_password_code, patient_password_reset, locale_set

urlpatterns = [
    path('register', patient_register, name='patient_register'),
    path('login', patient_login, name='patient_login'),
    path('check', patient_email_check, name='patient_email_check'),
    path('edit', patient_edit, name='patient_edit'),
    path('remove', patient_remove, name='patient_remove'),
    path('forget', patient_password_forget, name='patient_password_forget'),
    path('code', patient_password_code, name='patient_password_code'),
    path('reset', patient_password_reset, name='patient_password_reset'),
    path('locale', locale_set, name='locale_set'),

    path('refresh', token_refresh, name='token_refresh'),
]