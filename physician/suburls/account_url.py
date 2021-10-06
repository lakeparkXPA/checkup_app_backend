from django.urls import path
from physician.views import physician_register, physician_email_check, physician_login, physician_edit, token_refresh

urlpatterns = [
    path('register', physician_register, name='physician_register'),
    path('login', physician_login, name='physician_login'),
    path('check', physician_email_check, name='physician_email_check'),
    path('edit', physician_edit, name='physician_edit'),
    # path('remove', patient_remove, name='patient_remove'),
    #
    #
    path('refresh', token_refresh, name='token_refresh'),
]