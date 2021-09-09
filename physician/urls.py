from django.urls import path, include
from physician.views import get_main

urlpatterns = [
    path('account/', include('physician.suburls.account_url')),
    path('main', get_main, name='get_main')
    # path('fixed', Fixed.as_view()),
    # path('physicians', get_physicians, name='get_physicians'),

]