from django.urls import path, include

from graphene_django.views import GraphQLView
from patient.schema import schema
from patient.views import Daily, Fixed, get_physicians, generate_code

urlpatterns = [
    path('account/', include('patient.suburls.account_url')),
    path('fixed', Fixed.as_view()),
    path('daily', Daily.as_view()),
    path('physicians', get_physicians, name='get_physicians'),
    path('code', generate_code, name='generate_code'),


    path("graphql", GraphQLView.as_view(graphiql=True, schema=schema)),
]