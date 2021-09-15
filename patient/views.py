from django.db.models import Q, F
from django.core.validators import validate_email
from django.core.mail import EmailMessage

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, \
    HTTP_405_METHOD_NOT_ALLOWED, HTTP_205_RESET_CONTENT, HTTP_202_ACCEPTED
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from checkup_backend.settings import ALGORITHM, SECRET_KEY, FIREBASE_KEY
from checkup_backend.permissions import PatientAuthenticated

from patient.serializers import *
from patient.models import PLogin, PInfo, PFixed, PFixedUnique, PFixedCondition, PDaily, PDailyPredict, \
    PDailySymptom, PDailyTemperature, DPRelation, DUpdate, PPass

from tools import bool_dic, get_id, make_token, sendmail

import jwt
import datetime
import requests
import json
import random

# TODO ---- get daily update,



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
    	},
		required=['email', 'password1', 'password2'],
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
        p_user.save()

        p_fk = p_user
        p_detail = PInfo()
        p_detail.p = p_fk
        p_detail.name = name
        p_detail.save()

        return Response(status=HTTP_201_CREATED)
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Check account email.',
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
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
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
            id_cnt = PLogin.objects.get(email=email)
            raise ValueError('email_exist')
        except PLogin.DoesNotExist:
            res = Response({"success": True}, status=HTTP_200_OK)
            return res

    except Exception as e:
        if str(e) == 'email_exist':
            res = Response({"success": True}, status=HTTP_200_OK)
            return res
        else:
            res = Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)
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
    	},
		required=['email', 'password'],
	),
	responses={
		HTTP_200_OK: PatientLogin,
		HTTP_400_BAD_REQUEST: 'Bad request.',
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
                    token = PatientLogin(login_obj, many=True).data[0]

                    return Response(token, status=HTTP_202_ACCEPTED)

            except PLogin.DoesNotExist:
                raise ValueError('wrong_email')
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Refresh an auth-token.',
	method='post',
	responses={
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def token_refresh(request):
    token = request.META.get('HTTP_TOKEN')

    if not token:
        return Response({'message': 'no_token'}, status=HTTP_401_UNAUTHORIZED)

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, ALGORITHM)
        p_id = decoded_token['id']

        token = make_token(p_id)

        return Response({'token': token}, status=HTTP_201_CREATED)
    except:
        return Response({'message': 'token_expire'}, status=HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(
	operation_description='Edit account.',
	method='put',
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
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['PUT'])
@permission_classes((PatientAuthenticated,))
def patient_edit(request):
    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']
    name = request.data['name']

    token = request.META.get('HTTP_TOKEN')
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

        p_id = get_id(token)

        p_user = PLogin(p_id=p_id)
        p_user.email = email
        p_user.password = password1
        p_user.save()

        p_detail = PInfo(p=p_user)
        p_detail.name = name
        p_detail.save()

        return Response(status=HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Send email to find password.',
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
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_password_forget(request):
    email = request.data['email']

    try:
        if not email:
            raise ValueError('email_missing')
        try:
            p_email = PLogin.objects.get(email=email).email
        except PLogin.DoesNotExist:
            raise ValueError('email_nonexistent')

        code = random.randint(1, 10000)

        sendmail(
            to=p_email,
            subject='CheckUP Password Reset Confirmation Code.',
            message_text_html='CheckUp DOCL Password Reset<br>' +
                              'Your code to reset the password of CheckUp DOCL is <br><br><h2>' + str(code) +
                              '</h2><br><br> Please enter the site linked below and enter the code.<br>' +
                              'https://testapi.docl.org <br><br>Thank you,<br>Sincerely DOCL.'
        )
        p_id = PLogin.objects.get(email=email).p_id

        try:
            old_pass = PPass.objects.get(p=p_id)
            old_pass.delete()
        except PPass.DoesNotExist:
            password = PPass(p=p_id)
            password.code = code
            password.p_pass_time = datetime.datetime.now()
            password.save()

        return Response(status=HTTP_201_CREATED)

    except Exception as e:
        res = Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)
        return res


@swagger_auto_schema(
	operation_description='Check code to reset password.',
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
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def patient_password_code(request):
    email = request.data['email']
    code = request.data['code']

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
                raise ValueError('code_incorrect')
            code_time = password.p_pass_time
            time_passed = datetime.datetime.utcnow() - code_time

            if time_passed > datetime.timedelta(minutes=20):
                raise ValueError('time_expire')
            password.delete()
            return Response(status=HTTP_200_OK)

        except PPass.DoesNotExist:
            raise ValueError('code_nonexistent')

    except Exception as e:
        res = Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)
        return res


@swagger_auto_schema(
	operation_description='Reset password.',
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
    	},
		required=['email', 'password1', 'password2'],
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
def patient_password_reset(request):
    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']

    try:
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')

        try:
            id_cnt = PLogin.objects.get(email=email)

        except PLogin.DoesNotExist:
            raise ValueError('email_nonexistent')

        if password2 != password1:
            raise ValueError('password_not_same')

        p_user = PLogin(email=email)
        p_user.password = password1
        p_user.save()

        return Response(status=HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


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
    token = request.META.get('HTTP_TOKEN')
    p_id = get_id(token)

    patient_del = PLogin.objects.get(p_id=p_id)
    patient_del.delete()

    return Response(status=HTTP_200_OK)


class Fixed(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [PatientAuthenticated]

    @swagger_auto_schema(
        operation_description='Get fixed data.',
        responses={
            HTTP_200_OK: FixedGet,
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def get(self, request, format=None):
        token = request.META.get('HTTP_TOKEN')
        p_id = get_id(token)
        fixed = PFixed.objects.filter(p=p_id)

        return_dic = FixedGet(fixed, many=True).data[0]
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
                    description='Sex\n1: Male\n2: Female'
                ),
                'smoking': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Smoking type\n\
    						1: Never\n\
    						2: Stopped\n\
    						3: Smoking'
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
    						1: No Assist\n\
    						2: Partially-assisted\n\
    						3: Fully-assisted'
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
            required=['birth', 'sex', 'smoking', 'height', 'weight', 'adl', 'condition','unique'],
        ),
        responses={
            HTTP_201_CREATED: 'Fixed loaded',
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def post(self, request, format=None):
        token = request.META.get('HTTP_TOKEN')
        p_id = get_id(token)

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

        p_user = PLogin(p_id=p_id)

        try:
            id_cnt = PFixed.objects.get(p_id=p_id)
            return Response({'message': 'fixed_exist'}, status=HTTP_405_METHOD_NOT_ALLOWED)
        except PFixed.DoesNotExist:
            pass
        p_fixed = PFixed(p_id=p_id)

        p_fixed.save()
        p_detail = PInfo(p=p_user)

        res = Response(status=HTTP_201_CREATED)

        p_detail.birth = birth
        p_detail.sex = sex
        p_detail.save()

        p_fixed.weight = weight
        p_fixed.height = height
        p_fixed.adl = adl
        p_fixed.smoking = smoking
        p_fixed.p_fixed_date = datetime.datetime.utcnow()
        p_fixed.save()

        p_fixed_condition = PFixedCondition(p_fixed=p_fixed, **condition_data)
        p_fixed_condition.save()

        p_fixed_unique = PFixedUnique(p_fixed=p_fixed, **unique_data)
        p_fixed_unique.save()

        return res

    @swagger_auto_schema(
        operation_description='Update fixed data.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'birth': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Birth'
                ),
                'sex': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Sex\n1: Male\n2: Female'
                ),
                'smoking': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Smoking type\n\
    						1: Never\n\
    						2: Stopped\n\
    						3: Smoking'
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
    						1: No Assist\n\
    						2: Partially-assisted\n\
    						3: Fully-assisted'
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
            required=['birth', 'sex', 'smoking', 'height', 'weight', 'adl', 'condition','unique'],
        ),
        responses={
            HTTP_201_CREATED: 'Fixed loaded',
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def put(self,request, format=None):
        token = request.META.get('HTTP_TOKEN')
        p_id = get_id(token)

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

        p_user = PLogin(p_id=p_id)


        p_fixed = PFixed.objects.get(p_id=p_id)
        p_detail = PInfo.objects.get(p=p_user)
        res = Response(status=HTTP_200_OK)

        p_detail.birth = birth
        p_detail.sex = sex
        p_detail.save()

        p_fixed.weight = weight
        p_fixed.height = height
        p_fixed.adl = adl
        p_fixed.smoking = smoking
        p_fixed.p_fixed_date = datetime.datetime.utcnow()
        p_fixed.save()

        p_fixed_condition = PFixedCondition(p_fixed=p_fixed, **condition_data)
        p_fixed_condition.save()

        p_fixed_unique = PFixedUnique(p_fixed=p_fixed, **unique_data)
        p_fixed_unique.save()

        return res


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
            HTTP_200_OK: DailyGet,
            HTTP_401_UNAUTHORIZED: 'Bad request. No Token.',
        },
    )
    def get(self, request, format=None):
        token = request.META.get('HTTP_TOKEN')
        p_id = get_id(token)

        pageindex = int(request.GET.get('pageindex'))
        pageoffset = int(request.GET.get('pageoffset'))
        sort = request.GET.get('sort')
        start_date = datetime.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d') - datetime.timedelta(days=1)
        end_date = datetime.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d') + datetime.timedelta(days=1)

        order_lst = []
        if sort == 'high_temp':
            order_lst.append('-pdailytemperature__temp')
            order_lst.append('-p_daily_id')
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
        operation_description='Save daily data.',
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
        token = request.META.get('HTTP_TOKEN')
        p_id = get_id(token)

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
        data.update(p_fixed_condition)
        data.update(p_fixed_unique)
        data['temp'] = temp

        if temp_capable == 0:
            data['temp'] = 36.5
        if antipyretics > 0 and temp < 37.5:
            data['temp'] = 37.5

        prediction = json.loads(requests.get("https://model.docl.org/predict", json.dumps(data)).content)
        prediction_icu = json.loads(requests.get("https://model.docl.org/predict_icu", json.dumps(data)).content)
        prediction['icu'] = prediction_icu['probability']
        p_obj = PLogin.objects.get(p_id=p_id)
        p_daily = PDaily(p=p_obj)
        p_daily.p_daily_time = datetime.datetime.utcnow()
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
        p_daily_predict.prediction_result = prediction['ml_probability'] * 100
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
                d_update = DUpdate(relation=row['relation_id'])
                d_update.type = 1
                d_update.data = update_json
                d_update.seen = 0
                d_update.save()

                if row['d__push_token'] != "" and row['d__alert'] < 2:
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

        return Response(status=HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes((PatientAuthenticated,))
def get_physicians(request):
    token = request.META.get('HTTP_TOKEN')
    p_id = get_id(token)

    phy = DPRelation.objects.select_related('d').filter(p=p_id).order_by('add_time').\
        values('d_id', 'p_id', 'add_time', 'd__name', 'd__nation', 'd__region', 'd__hospital')

    phy_lst = []
    for row in phy:
        row_dic = row
        row_dic['code'] = row_dic['p_id'] + 1000
        phy_lst.append(row_dic)

    return Response(phy_lst, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes((PatientAuthenticated,))
def generate_code(request):
    token = request.META.get('HTTP_TOKEN')
    p_id = get_id(token)
    # TODO ---- change to setting code generation number
    return Response({'code': p_id + 1000}, status=HTTP_201_CREATED)


