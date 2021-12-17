from django.db.models import Q
from django.core.validators import validate_email

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, \
    HTTP_405_METHOD_NOT_ALLOWED, HTTP_205_RESET_CONTENT, HTTP_202_ACCEPTED, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from checkup_backend.settings import ALGORITHM, SECRET_KEY, FIREBASE_KEY, PATIENT_CODE
from checkup_backend.permissions import PatientAuthenticated, PatientResetAuthenticated

from patient.serializers import *
from patient.models import PLogin, PInfo, PFixed, PFixedUnique, PFixedCondition, PDaily, PDailyPredict, \
    PDailySymptom, PDailyTemperature, DPRelation, DUpdate, PPass

from tools import bool_dic, get_id, make_token, sendmail
from checkup_backend import error_collection

import jwt
import datetime
import requests
import json
import random
import copy


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
            'agreed':  openapi.Schema(
					type=openapi.TYPE_BOOLEAN,
					description='Agreed'),
            'name': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Name'),
            'push_token': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Push token'),
    	},
		required=['email', 'password1', 'password2'],
	),
	responses={
		HTTP_201_CREATED: '\n\n> **회원가입, 토큰 반환**\n\n```\n{\n\n\t"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0",\n\t"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0"\n\n}\n\n```',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_MISSING.as_md() +
        error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
        error_collection.RAISE_400_EMAIL_EXIST.as_md() +
        error_collection.RAISE_400_PASSWORD_NOT_SAME.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_register(request):
    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']
    agreed = request.data['agreed']

    name = request.data['name']
    try:
        if not email:
            raise ValueError('email_missing')
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        else:
            try:
                id_cnt = PLogin.objects.get(email=email)
                raise ValueError('email_exist')
            except PLogin.DoesNotExist:
                pass
        if password2 != password1:
            raise ValueError('password_not_same')

        p_user = PLogin()
        p_user.email = email
        p_user.password = password1
        p_user.agreed = agreed
        try:
            push_token = request.data['push_token']
            if push_token:
                p_user.push_token = push_token
        except:
            pass
        p_user.save()

        p_fk = p_user
        p_detail = PInfo(p=p_user)
        p_detail.p = p_fk
        p_detail.name = name
        p_detail.save()
        login_obj = PLogin.objects.filter(email=email)
        token = PatientLogin(login_obj, many=True).data[0]

        p_user.refresh_token = token['refresh_token'].decode()
        p_user.save()

        return Response(token, status=HTTP_201_CREATED)
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Check email duplication for account register.',
	method='post',
	request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
    	properties={
        	'email': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Email'),
    	},
		required=['email'],
	),
	responses={
		HTTP_200_OK: 'registrable: True/False',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_EMAIL_MISSING.as_md() +
            error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
            error_collection.RAISE_400_EMAIL_EXIST.as_md()
        ,
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_email_check(request):
    email = request.data['email']

    try:
        if not email:
            raise ValueError('email_missing')
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        try:
            id_cnt = PLogin.objects.get(email=email)
            res = Response({"registrable": False}, status=HTTP_200_OK)
            return res
        except PLogin.DoesNotExist:
            res = Response({"registrable": True}, status=HTTP_200_OK)
            return res

    except Exception as e:
        res = Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)
        return res



@swagger_auto_schema(
	operation_description='Return an auth-token for the user account.',
	method='post',
	request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'email': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Email'),
        	'password': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password'),
            'push_token': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Push token'),
    	},
		required=['email', 'password'],
	),
	responses={
		HTTP_200_OK: '\n\n> **로그인, 토큰 반환**\n\n```\n{\n\n\t"basic_info":True\n\t"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0",\n\t"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0"\n\n}\n\n```',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
        error_collection.RAISE_400_WRONG_PASSWORD.as_md() +
        error_collection.RAISE_400_WRONG_EMAIL.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_login(request):
    email = request.data['email']
    password = request.data['password']
    login_obj = PLogin.objects.filter(email=email)

    try:
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        else:
            try:
                db_pass = login_obj.get().password

                if db_pass != password:
                    raise ValueError('wrong_password')
                else:

                    try:
                        push_token = request.data['push_token']
                        if push_token:
                            p_user = PLogin.objects.get(email=email)
                            p_user.push_token = push_token
                            p_user.save()
                    except:
                        pass

                    token = PatientLogin(login_obj, many=True).data[0]

                    try:
                        p_user = PLogin.objects.get(email=email)
                        p_fixed = PFixed.objects.get(p=p_user.p_id)
                        basic_info = True
                    except PFixed.DoesNotExist:
                        basic_info = False
                    token['basic_info'] = basic_info

                    p_user = PLogin.objects.get(email=email)
                    p_user.refresh_token = token['refresh_token'].decode()
                    p_user.save()

                    return Response(token, status=HTTP_202_ACCEPTED)

            except PLogin.DoesNotExist:
                raise ValueError('wrong_email')
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Refresh an auth-token.',
	method='post',
	responses={
		HTTP_200_OK: '\n\n> **신규 토큰 반환**\n\n```\n{\n\n\t"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0",\n\t"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0"\n\n}\n\n```',
		HTTP_401_UNAUTHORIZED:
            error_collection.RAISE_401_NO_REFRESH_TOKEN.as_md() +
            error_collection.RAISE_401_NO_TOKEN.as_md() +
            error_collection.RAISE_401_WRONG_REFRESH_TOKEN.as_md() +
            error_collection.RAISE_401_REFRESH_TOKEN_EXPIRE.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def token_refresh(request):
    token = request.META.get('HTTP_TOKEN')
    refresh_token = request.META.get('HTTP_REFRESH_TOKEN')

    if not refresh_token:
        return Response({'message': 'no_refresh_token'}, status=HTTP_401_UNAUTHORIZED)

    if not token:
        return Response({'message': 'no_token'}, status=HTTP_401_UNAUTHORIZED)

    try:
        client_decoded = jwt.decode(refresh_token, SECRET_KEY, ALGORITHM)
        p_id = client_decoded['id']
        p_user = PLogin.objects.get(p_id=p_id)
        db_refresh_token = p_user.refresh_token
        db_decoded = jwt.decode(db_refresh_token, SECRET_KEY, ALGORITHM)
        if db_decoded['auth'] and client_decoded['auth'] == 'refresh' and client_decoded == db_decoded:
            login_obj = PLogin.objects.filter(p_id=p_id)
            token = PatientLogin(login_obj, many=True).data[0]

            p_user.refresh_token = token['refresh_token'].decode()
            p_user.save()

            return Response(token, status=HTTP_201_CREATED)
        else:
            return Response({'message': 'wrong_refresh_token'}, status=HTTP_401_UNAUTHORIZED)
    except:
        return Response({'message': 'refresh_token_expire'}, status=HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(
	operation_description='Edit account.',
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
            'name': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Name'),
    	},
		required=['email', 'password1', 'password2'],
	),
	responses={
		HTTP_201_CREATED: 'Edited.',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_MISSING.as_md() +
        error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
        error_collection.RAISE_400_EMAIL_EXIST.as_md() +
        error_collection.RAISE_400_PASSWORD_NOT_SAME.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PatientAuthenticated,))
def patient_edit(request):
    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']
    name = request.data['name']


    try:
        if not email:
            raise ValueError('email_missing')
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')

        if password2 != password1:
            raise ValueError('password_not_same')

        p_id = get_id(request)

        p_user = PLogin.objects.get(p_id=p_id)
        p_user.email = email
        p_user.password = password1
        p_user.save()

        p_detail = PInfo.objects.get(p=p_user)
        p_detail.name = name
        p_detail.save()

        return Response(status=HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Send email a code to find password. Code expires in 20 minutes.',
	method='post',
    request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Email'),
            },
            required=['email'],
    ),
	responses={
		HTTP_201_CREATED: 'Email sent.',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_MISSING.as_md() +
        error_collection.RAISE_400_EMAIL_NONEXISTENT.as_md()
        ,
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_password_forgot(request):
    email = request.data['email']

    try:
        if not email:
            raise ValueError('email_missing')
        try:
            p_email = PLogin.objects.get(email=email).email
        except PLogin.DoesNotExist:
            raise ValueError('email_nonexistent')

        code = random.randint(1000, 10000)

        sendmail(
            to=p_email,
            subject='CheckUP Password Reset Confirmation Code.',
            message_text_html='CheckUp DOCL Password Reset<br>' +
                              'Your code to reset the password of CheckUp DOCL is <br><br><h2>' + str(code) +
                              '</h2><br><br> Please enter the site linked below and enter the code.<br>' +
                              'https://covid.docl.org <br><br>Thank you,<br>Sincerely DOCL.'
        )
        p_obj = PLogin.objects.get(email=email)
        p_id = p_obj.p_id
        try:
            old_pass = PPass.objects.get(p=p_id)
            old_pass.delete()
        except PPass.DoesNotExist:
            pass
        password = PPass(p=p_obj)
        password.code = code
        password.p_pass_time = datetime.datetime.now()
        password.save()

        return Response(status=HTTP_201_CREATED)

    except Exception as e:
        res = Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)
        return res


@swagger_auto_schema(
	operation_description='Check email given password reset code. Code expires in 20 minutes.',
	method='get',
    manual_parameters=[
        openapi.Parameter(
            'email',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description='Email'
        ),
        openapi.Parameter(
            'code',
            openapi.IN_QUERY,
            type=openapi.TYPE_NUMBER,
            description='Code'
        ),
    ],
	responses={
		HTTP_200_OK: 'registrable: True/False, token : token',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_CODE_MISSING.as_md() +
        error_collection.RAISE_400_WRONG_CODE.as_md() +
        error_collection.RAISE_400_TIME_EXPIRE.as_md() +
        error_collection.RAISE_400_CODE_NONEXISTENT.as_md(),
	},
)
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def patient_password_code(request):
    email = request.GET.get('email')
    code = int(request.GET.get('code'))

    try:
        if not code:
            raise ValueError('code_missing')

        try:
            p_id = PLogin.objects.get(email=email).p_id
        except PLogin.DoesNotExist:
            raise ValueError('email_nonexistent')

        try:
            password = PPass.objects.get(p=p_id)
            old_code = password.code

            if old_code != code:
                raise ValueError('wrong_code')
            code_time = password.p_pass_time
            time_passed = datetime.datetime.now(datetime.timezone.utc) - code_time

            if time_passed > datetime.timedelta(minutes=20):
                raise ValueError('time_expire')
            password.delete()
            token = make_token(p_id, auth='patient_reset')
            return Response({"registrable": True, "reset_token": token}, status=HTTP_200_OK)

        except PPass.DoesNotExist:
            raise ValueError('code_nonexistent')

    except Exception as e:
        res = Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)
        return res


@swagger_auto_schema(
	operation_description='Reset password.',
	method='post',
	request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'password1': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password1'),
            'password2': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password2'),
    	},
		required=['password1', 'password2'],
	),
	responses={
		HTTP_201_CREATED: openapi.Schema(
				type=openapi.TYPE_STRING,
				decription='auth-token'),
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
        error_collection.RAISE_400_EMAIL_NONEXISTENT.as_md() +
        error_collection.RAISE_400_PASSWORD_NOT_SAME.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PatientResetAuthenticated,))
def patient_password_reset(request):
    p_id = get_id(request)
    password1 = request.data['password1']
    password2 = request.data['password2']

    try:
        try:
            p_user = PLogin.objects.get(p_id=p_id)

        except PLogin.DoesNotExist:
            raise ValueError('email_nonexistent')

        if password2 != password1:
            raise ValueError('password_not_same')

        p_user.password = password1
        p_user.save()

        return Response(status=HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Delete account',
	method='delete',
	responses={
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['DELETE'])
@permission_classes((PatientAuthenticated,))
def patient_remove(request):
    p_id = get_id(request)

    patient_del = PLogin.objects.get(p_id=p_id)
    patient_del.delete()

    return Response(status=HTTP_200_OK)


class Fixed(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [PatientAuthenticated]

    @swagger_auto_schema(
        operation_description='Get fixed data.',
        responses={
            HTTP_200_OK: '\n\n> **고정 변수 반환 (반환 예 하단 참고)**\n\n```\n{\n\n\t"p_fixed_id": 7,\n\t"smoking": 1,\n\t"height": 182.0,\n\t"weight": 102.0,\n\t"adl": 0,\n\t"p_id": 19,\n\t"chronic_cardiac_disease": 1,\n\t"chronic_neurologic_disorder": 1,\n\t"copd": 1,\n\t"asthma": 1,\n\t"chronic_liver_disease": 1,\n\t"hiv": 1,\n\t"autoimmune_disease": 1,\n\t"dm": 0,\n\t"hypertension": 0,\n\t"ckd": 0,\n\t"cancer": 0,\n\t"heart_failure": 0,\n\t"dementia": 0,\n\t"chronic_hematologic_disorder": 0,\n\t"transplantation": 1,\n\t"immunosuppress_agent": 1,\n\t"chemotherapy": 0,\n\t"pregnancy": 0,\n\t"name": null,\n\t"birth": "1992-12-25",\n\t"sex": 0,\n\t"email": "test@docl.org"\n\n}\n\n```',
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def get(self, request, format=None):
        p_id = get_id(request)
        fixed = PFixed.objects.filter(p=p_id)

        fixed_get = FixedGet(fixed, many=True).data
        if fixed_get:
            return_dic = fixed_get[0]
        else:
            return_dic = {}
        return Response(return_dic, status=HTTP_200_OK)

    @swagger_auto_schema(
        operation_description='Save fixed data.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'birth': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Birth'
                ),
                'sex': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Sex\n0: Male\n1: Female'
                ),
                'smoking': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Smoking type\n\
    						0: Never\n\
    						1: Stopped\n\
    						2: Smoking'
                ),
                'height': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Height'
                ),
                'weight': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Weight'
                ),
                'adl': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Adl type\n\
    						0: No Assist\n\
    						1: Partially-assisted\n\
    						2: Fully-assisted'
                ),
                'condition': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='chronic_cardiac_disease\n\
                    chronic_neurologic_disorder\n\
                    copd\n\
                    asthma\n\
                    chronic_liver_disease\n\
                    hiv\n\
                    autoimmune_disease\n\
                    dm\n\
                    hypertension\n\
                    ckd\n\
                    cancer\n\
                    heart_failure\n\
                    dementia\n\
                    chronic_hematologic_disorder'
                ),
                'unique': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='transplantation\n\
                    immunosuppress_agent\n\
                    chemotherapy\n\
                    pregnancy'
                ),
            },
            required=['birth', 'sex', 'smoking', 'height', 'weight', 'adl', 'condition', 'unique'],
        ),
        responses={
            HTTP_201_CREATED: 'Fixed loaded',
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def post(self, request, format=None):
        p_id = get_id(request)

        birth = request.data['birth']
        sex = request.data['sex']

        smoking = request.data['smoking']
        height = request.data['height']
        weight = request.data['weight']
        adl = request.data['adl']

        condition = request.data['condition']
        condition_lst = ['chronic_cardiac_disease', 'chronic_neurologic_disorder', 'copd', 'asthma',
                         'chronic_liver_disease', 'hiv', 'autoimmune_disease', 'dm', 'hypertension', 'ckd', 'cancer',
                         'heart_failure', 'dementia', 'chronic_hematologic_disorder']
        unique = request.data['unique']
        unique_lst = ['transplantation', 'immunosuppress_agent', 'chemotherapy', 'pregnancy']

        condition_data = bool_dic(condition, condition_lst)
        unique_data = bool_dic(unique, unique_lst)



        try:
            p_fixed = PFixed.objects.get(p=p_id)
            p_detail = PInfo.objects.get(p=p_id)
            p_fixed_condition_id = PFixedCondition.objects.get(p_fixed=p_fixed.p_fixed_id).p_fixed_condition_id
            p_fixed_unique_id = PFixedUnique.objects.get(p_fixed=p_fixed.p_fixed_id).p_fixed_unique_id

            p_fixed_condition = PFixedCondition(p_fixed_condition_id=p_fixed_condition_id, p_fixed=p_fixed, **condition_data)
            p_fixed_unique = PFixedUnique(p_fixed_unique_id=p_fixed_unique_id, p_fixed=p_fixed, **unique_data)

        except PFixed.DoesNotExist:
            p_user = PLogin.objects.get(p_id=p_id)
            p_fixed = PFixed(p=p_user)
            p_fixed.save()

            p_detail = PInfo.objects.get(p=p_id)
            p_fixed_condition = PFixedCondition(p_fixed=p_fixed, **condition_data)
            p_fixed_unique = PFixedUnique(p_fixed=p_fixed, **unique_data)

        p_detail.birth = birth
        p_detail.sex = sex
        p_detail.save()

        p_fixed.weight = weight
        p_fixed.height = height
        p_fixed.adl = adl
        p_fixed.smoking = smoking
        p_fixed.p_fixed_date = datetime.datetime.utcnow()
        p_fixed.save()

        p_fixed_condition.save()
        p_fixed_unique.save()

        return Response(status=HTTP_201_CREATED)


class Daily(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [PatientAuthenticated]

    @swagger_auto_schema(
        operation_description='Get daily data.',
        manual_parameters=[
            openapi.Parameter(
                'pageindex',
                openapi.IN_QUERY,
                type=openapi.TYPE_NUMBER,
                description='Page index'
            ),
            openapi.Parameter(
                'pageoffset',
                openapi.IN_QUERY,
                type=openapi.TYPE_NUMBER,
                description='Page offset'
            ),
            openapi.Parameter(
                'sort',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='outdated, latest, high_temp'
            ),
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Daily checkup start date.'
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Daily checkup end date.'
            ),

        ],
        responses={
            HTTP_200_OK: '\n\n> **일별 변수 반환 (반환 예 하단 참고)**\n\n```\n{\n\n\t"hasnext": 2,\n\t"items": [\n\t\t{\n\t\t\t"p_daily_id": 5,\n\t\t\t"p_daily_time": "2021-09-15T07:55:39Z",\n\t\t\t"latitude": 0.0,\n\t\t\t"longitude": 0.0,\n\t\t\t"p_id": 19,\n\t\t\t"hemoptysis": 0,\n\t\t\t"dyspnea": 0,\n\t\t\t"chest_pain": 0,\n\t\t\t"cough": 0,\n\t\t\t"sputum": 0,\n\t\t\t"rhinorrhea": 0,\n\t\t\t"sore_throat": 0,\n\t\t\t"anosmia": 0,\n\t\t\t"myalgia": 0,\n\t\t\t"arthralgia": 0,\n\t\t\t"fatigue": 0,\n\t\t\t"headache": 0,\n\t\t\t"diarrhea": 0,\n\t\t\t"nausea_vomiting": 0,\n\t\t\t"chill": 0,\n\t\t\t"antipyretics": 1,\n\t\t\t"temp_capable": 1,\n\t\t\t"temp": 36.5,\n\t\t\t"prediction_result": 44.002,\n\t\t\t"prediction_explaination": "{\"ml_class\": 1, \"ml_probability\": 0.440020352602005, \"stat_class\": 1, \"stat_probability\": 1.3409791840000034, \"status\": \"ok\", \"icu\": 0.4943764805793762}",\n\t\t\t"oxygen": 0.44002,\n\t\t\t"icu": 0.494376\n\t\t},\n\t\t{\n\t\t\t"p_daily_id": 6,\n\t\t\t"p_daily_time": "2021-09-15T07:55:47Z",\n\t\t\t"latitude": 0.0,\n\t\t\t"longitude": 0.0,\n\t\t\t"p_id": 19,\n\t\t\t"hemoptysis": 0,\n\t\t\t"dyspnea": 0,\n\t\t\t"chest_pain": 0,\n\t\t\t"cough": 0,\n\t\t\t"sputum": 0,\n\t\t\t"rhinorrhea": 0,\n\t\t\t"sore_throat": 0,\n\t\t\t"anosmia": 0,\n\t\t\t"myalgia": 0,\n\t\t\t"arthralgia": 0,\n\t\t\t"fatigue": 0,\n\t\t\t"headache": 0,\n\t\t\t"diarrhea": 0,\n\t\t\t"nausea_vomiting": 0,\n\t\t\t"chill": 0,\n\t\t\t"antipyretics": 1,\n\t\t\t"temp_capable": 1,\n\t\t\t"temp": 37.5,\n\t\t\t"prediction_result": 44.002,\n\t\t\t"prediction_explaination": "{\"ml_class\": 1, \"ml_probability\": 0.440020352602005, \"stat_class\": 1, \"stat_probability\": 1.3409791840000034, \"status\": \"ok\", \"icu\": 0.4943764805793762}",\n\t\t\t"oxygen": 0.44002,\n\t\t\t"icu": 0.494376\n\t\t}\n\t]\n\n}\n\n```',

            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def get(self, request, format=None):
        p_id = get_id(request)

        pageindex = int(request.GET.get('pageindex'))
        pageoffset = int(request.GET.get('pageoffset'))
        sort = request.GET.get('sort')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = datetime.datetime.now() - datetime.timedelta(days=8)
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.datetime.now()

        order_lst = []
        if sort == 'high_temp':
            order_lst.append('-p_daily_id')
            order_lst.append('-pdailytemperature__temp')
        elif sort == 'latest':
            order_lst.append('-p_daily_id')
        else:
            order_lst.append('p_daily_id')

        daily = PDaily.objects.prefetch_related('pdailytemperature_set').\
            filter(Q(p=p_id) & Q(p_daily_time__range=(start_date, end_date))).order_by(*order_lst)
        daily_lst = DailyGet(daily, many=True).data
        page_num, last_num = divmod(len(daily_lst), pageoffset)

        if pageindex == 0:
            daily_paginated = daily_lst[:pageoffset]
            if page_num == 0:
                hasnext = 0
            elif page_num-1 == pageindex:
                hasnext = last_num
            else:
                hasnext = pageoffset
        elif pageindex == page_num:
            if last_num == 0:
                daily_paginated = daily_lst[-pageoffset:]
            else:
                daily_paginated = daily_lst[-last_num:]
            hasnext = 0
        elif pageindex > page_num:
            hasnext = 0
            daily_paginated = []
        else:
            daily_paginated = daily_lst[pageindex*pageoffset: (pageindex+1)*pageoffset]
            if page_num == pageindex:
                hasnext = last_num
            else:
                hasnext = pageoffset

        daily_get = {}
        daily_get['hasnext'] = hasnext
        daily_get['items'] = daily_paginated

        return Response(daily_get, status=HTTP_200_OK)

    @swagger_auto_schema(
        operation_description='Save or edit daily data. (If record exist edit, else save)',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'latitude': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Body temperature'
                ),
                'longitude': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Body temperature'
                ),
                'symptom': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='Symptom\n\n\
                    hemoptysis\n\
                    dyspnea\n\
                    chest_pain\n\
                    cough\n\
                    sputum\n\
                    rhinorrhea\n\
                    sore_throat\n\
                    anosmia\n\
                    myalgia\n\
                    arthralgia\n\
                    fatigue\n\
                    headache\n\
                    diarrhea\n\
                    nausea_vomiting\n\
                    chill'
                ),
                'temp': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Body temperature'
                ),
                'antipyretics': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Have you taken fever-reducers or painkillers?'
                ),
                'temp_capable': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Can you check your temperature?'
                ),
            },
            required=['latitude', 'longitude', 'symptoms', 'temp', 'antipyretics', 'temp_capable'],
        ),
        responses={
            HTTP_201_CREATED: 'ok',
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def post(self, request, format=None):

        p_id = get_id(request)

        latitude = request.data['latitude']
        longitude = request.data['longitude']

        antipyretics = request.data['antipyretics']
        temp_capable = request.data['temp_capable']
        temp = request.data['temp']

        symptom = request.data['symptom']
        symptom_lst = ['hemoptysis', 'dyspnea', 'chest_pain', 'cough', 'sputum', 'rhinorrhea', 'sore_throat', 'anosmia',
                       'myalgia', 'arthralgia', 'fatigue', 'headache', 'diarrhea', 'nausea_vomiting', 'chill']
        symptom_data = bool_dic(symptom, symptom_lst)

        p_fixed = PFixed.objects.get(p_id=p_id)
        p_fixed_condition = list(PFixedCondition.objects.filter(p_fixed_id=p_fixed). \
                                 values('chronic_cardiac_disease', 'chronic_neurologic_disorder', 'copd', 'asthma',
                                        'chronic_liver_disease', 'hiv', 'autoimmune_disease', 'dm', 'hypertension',
                                        'ckd',
                                        'cancer', 'heart_failure', 'dementia', 'chronic_hematologic_disorder'))[0]
        p_fixed_unique = list(PFixedUnique.objects.filter(p_fixed_id=p_fixed).
                              values('transplantation', 'immunosuppress_agent', 'chemotherapy', 'pregnancy'))[0]

        data = {}
        data.update(symptom_data)
        if temp:
            data['temp'] = float(temp)
        else:
            data['temp'] = 36.5
        return_data = copy.deepcopy(data)

        data.update(p_fixed_condition)
        data.update(p_fixed_unique)
        data['smoking'] = p_fixed.smoking
        data['adl'] = p_fixed.adl
        data['lethalgic'] = 0

        p_info = PInfo.objects.get(p=p_id)
        born = p_info.birth
        today = datetime.datetime.today()

        data['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        data['sex'] = p_info.sex
        data['age'] = 10

        data['mentality'] = None

        if temp_capable == 0:
            data['temp'] = 36.5
        if antipyretics > 0 and data['temp'] < 37.5:
            data['temp'] = 37.5

        prediction = json.loads(requests.get("https://model.docl.org/predict", params=data).content)
        prediction_icu = json.loads(requests.get("https://model.docl.org/predict_icu", params=data).content)
        prediction['icu'] = prediction_icu['probability']

        return_dic = {}
        return_dic['result'] = prediction['ml_probability']
        prediction_result = prediction['ml_probability'] * 100
        recorded_time = datetime.datetime.utcnow()

        return_data['prediction_result'] = prediction_result
        return_data['prediction_explaination'] = json.dumps(prediction)
        return_data['p_daily_time'] = recorded_time
        return_data['temp'] = temp
        return_dic['data'] = return_data

        p_obj = PLogin.objects.get(p_id=p_id)
        p_daily = PDaily(p=p_obj)
        p_daily.p_daily_time = recorded_time
        p_daily.latitude = latitude
        p_daily.longitude = longitude
        p_daily.save()

        p_daily_symptom = PDailySymptom(p_daily=p_daily, **symptom_data)
        p_daily_symptom.save()

        p_daily_temp = PDailyTemperature(p_daily=p_daily)
        p_daily_temp.antipyretics = antipyretics
        p_daily_temp.temp_capable = temp_capable
        p_daily_temp.temp = temp
        p_daily_temp.save()

        p_daily_predict = PDailyPredict(p_daily=p_daily)
        p_daily_predict.prediction_result = prediction_result
        p_daily_predict.prediction_explaination = json.dumps(prediction)
        p_daily_predict.oxygen = prediction['ml_probability']
        p_daily_predict.icu = prediction['icu']
        p_daily_predict.save()

        previous_id_lst = list(PDaily.objects.filter(p_id=p_id).order_by('-p_daily_time').values('p_daily_id'))

        update_data = {}
        if len(previous_id_lst) > 1:
            previous_icu = PDailyPredict.objects.get(p_daily_id=previous_id_lst[1]['p_daily_id']).prediction_explaination
            previous_icu_decode = json.loads(previous_icu)
            update_data['oxygen'] = prediction['ml_probability'] - previous_icu_decode['ml_probability']
            update_data['icu'] = prediction['icu'] - previous_icu_decode['icu']
        else:
            update_data['oxygen'] = 0
            update_data['icu'] = 0

        doc_lst = DPRelation.objects.select_related('d').select_related('p').filter(Q(p=p_id) & Q(discharged=0)). \
            values('relation_id', 'p__pinfo__name', 'd_id', 'd__push_token', 'd__alert')
        tokens = []
        if doc_lst:
            update_data['name'] = doc_lst[0]['p__pinfo__name']

            for row in doc_lst:
                update_json = json.dumps(update_data)
                dp_relation = DPRelation.objects.get(relation_id=row['relation_id'])
                d_update = DUpdate(relation=dp_relation)
                d_update.type = 1
                d_update.data = update_json
                d_update.seen = 0
                d_update.recorded_time = datetime.datetime.now()
                d_update.save()

                if not row['d__push_token'] and not row['d__alert']:
                    if row['d__alert'] < 2:
                        if (update_data['oxygen'] > 0 or update_data['icu']) or row['d__alert'] == 0:
                            tokens.append(row['d__push_token'])

            if len(tokens) > 0:
                pushbody = "O2 probability "
                if round(100 * update_data['oxygen']) < 0:
                    pushbody += "improved by " + str(round((-100) * update_data['oxygen'])) + "% and "
                elif round(100 * update_data['oxygen']) > 0:
                    pushbody += "worsened by " + str(round(100 * update_data['oxygen'])) + "% and "
                else:
                    pushbody += "is the same and "

                pushbody += "ICU probability "

                if round(100 * update_data['icu']) < 0:
                    pushbody += "improved by " + str(round((-100) * update_data['icu'])) + "%."
                elif round(100 * update_data['icu']) > 0:
                    pushbody += "worsened by " + str(round(100 * update_data['icu'])) + "%."
                else:
                    pushbody += "is the same."

                url = 'https://fcm.googleapis.com/fcm/send'

                headers = {
                    'Authorization': 'key=' + FIREBASE_KEY,
                    'Content-Type': 'application/json; UTF-8',
                }
                contents = {
                    'registration_ids': tokens,
                    'notification': {
                        'title': str(update_data['name']) + ' has done a new check-up',
                        'body': pushbody
                    }
                }
                requests.post(url, data=json.dumps(contents), headers=headers)
        else:
            pass

        return Response(return_dic, status=HTTP_201_CREATED)


@swagger_auto_schema(
	operation_description='Set locale for account. ex) kr, en, ja, id',
	method='post',
    request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'locale': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Locale'),
            },
            required=['locale'],
    ),
	responses={
		HTTP_201_CREATED: 'Locale set.'
        ,
	},
)
@api_view(['POST'])
@permission_classes((PatientAuthenticated,))
def locale_set(request):
    p_id = get_id(request)
    locale = request.data['locale']

    p = PLogin.objects.get(p_id=p_id)
    p.locale = locale
    p.save()

    return Response(status=HTTP_200_OK)



@swagger_auto_schema(
	operation_description='Get linked physician list.',
	method='get',
	responses={
		HTTP_200_OK: '\n\n> **연동된 의사 목록 반환 (반환 예 하단 참고)**\n\n```\n{\n\n\t"d_id":1,\n\t"p_id":5,\n\t"add_time":"2021-09-29 04:19:23",\n\t"d__name":"DOCL",\n\t"d__nation":"korea",\n\t"d__region":"seoul",\n\t"d_hospital":"sev",\n\t"code":1005\n\n}\n\n```',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['GET'])
@permission_classes((PatientAuthenticated,))
def get_physicians(request):
    p_id = get_id(request)

    phy = DPRelation.objects.select_related('d').filter(p=p_id).exclude(discharged=1).order_by('add_time').\
        values('d_id', 'p_id', 'add_time', 'd__name', 'd__nation', 'd__region', 'd__hospital')

    phy_lst = []
    for row in phy:
        row_dic = row
        row_dic['code'] = row_dic['p_id'] + PATIENT_CODE
        phy_lst.append(row_dic)

    return Response(phy_lst, status=HTTP_200_OK)


@swagger_auto_schema(
	operation_description='Generate code to link physician.',
	method='get',
	responses={
		HTTP_201_CREATED: '\n\n> **의사 연동 코드 생성**\n\n```\n{\n\n\t"code": "1005"\n\n}\n\n```',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['GET'])
@permission_classes((PatientAuthenticated,))
def generate_code(request):
    p_id = get_id(request)
    p = PLogin.objects.get(p_id=p_id)
    p.code_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    p.save()
    return Response({'code': p_id + PATIENT_CODE}, status=HTTP_201_CREATED)


