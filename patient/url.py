from django.urls import path, include
from graphene_django.views import GraphQLView
from patient.schema import schema

urlpatterns = [
    path('account/', include('patient.urls.account_url')),
    path("graphql", GraphQLView.as_view(graphiql=True, schema=schema)),
]