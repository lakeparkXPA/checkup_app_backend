from django.db.models import Q, F
from django.core.validators import validate_email

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, \
    HTTP_405_METHOD_NOT_ALLOWED
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from checkup_backend.settings import ALGORITHM, SECRET_KEY, FIREBASE_KEY
from checkup_backend.permissions import PatientAuthenticated

from physician.serializers import *
from physician.models import DLogin

from tools import make_token, get_id

import jwt
import datetime
import requests
import json

# TODO ---- 의료진 환자 추가 시 push 알림


@swagger_auto_schema(
	operation_description='Register account.',
	method='post',
	request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'email': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Email'),
        	'password1': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password1'),
            'password2': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password2'),
            'country':  openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Country'),
            'region':  openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Region'),
            'hospital':  openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Hospital'),
            'name': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Name'),
    	},
		required=['email', 'password'],
	),
	responses={
		HTTP_201_CREATED: openapi.Schema(
				type=openapi.TYPE_STRING,
				decription='auth-token'),
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def physician_register(request):
    data = dict(request.data)

    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']

    try:
        if not email:
            raise ValueError('email_missing')
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        else:
            try:
                id_cnt = DLogin.objects.get(email=email)
                raise ValueError('email_exist')
            except DLogin.DoesNotExist:
                pass
        if password2 != password1:
            raise ValueError('password_not_same')

        data['password'] = password1
        data['nation'] = data['country']

        data.pop('country')
        data.pop('password1')
        data.pop('password2')


        d_serial = DLoginSerializer(data=data)

        if d_serial.is_valid():
            d_serial.save()
            return Response(status=HTTP_201_CREATED)
        else:
            return Response(d_serial.errors, status=HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


