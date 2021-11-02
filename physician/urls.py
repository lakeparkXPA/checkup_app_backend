from django.urls import path, include
from physician.views import get_main, add_patient, get_fixed, physician_discharge, physician_patient, get_updates, \
    send_alert, set_oxygen

urlpatterns = [
    path('account/', include('physician.suburls.account_url')),
    path('main', get_main, name='get_main'),
    path('add', add_patient, name='add_patient'),
    path('fixed', get_fixed, name='get_fixed'),
    path('discharge', physician_discharge, name='get_fixed'),
    path('patient', physician_patient, name='physician_patient'),
    path('updates', get_updates, name='get_updates'),
    path('send', send_alert, name='send_alert'),
    path('oxygen', set_oxygen, name='set_oxygen'),
    # path('physicians', get_physicians, name='get_physicians'),

]