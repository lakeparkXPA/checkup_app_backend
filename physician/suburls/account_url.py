from django.urls import path
from physician.views import physician_register, physician_email_check

urlpatterns = [
    path('register', physician_register, name='physician_register'),
    # path('login', patient_login, name='patient_login'),
    path('check', physician_email_check, name='physician_email_check'),
    # path('edit', patient_edit, name='patient_edit'),
    # path('remove', patient_remove, name='patient_remove'),
    #
    #
    # path('refresh', token_refresh, name='token_refresh'),
]