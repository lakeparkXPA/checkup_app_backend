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
from checkup_backend.permissions import PhysicianAuthenticated

from physician.serializers import *
from patient.models import DLogin, DPRelation, DUpdate, PDailyPredict, DOxygen

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
def physician_email_check(request):
    email = request.data['email']

    try:
        if not email:
            raise ValueError('email_missing')
        try:
            id_cnt = DLogin.objects.get(email=email)
            raise ValueError('email_exist')
        except DLogin.DoesNotExist:
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
		HTTP_200_OK: PhysicianLogin,
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def physician_login(request):
    email = request.data['email']
    password = request.data['password']
    login_obj = DLogin.objects.filter(email=email)
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
                    token = PhysicianLogin(login_obj, many=True).data[0]

                    return Response(token, status=HTTP_200_OK)

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

        token = make_token(p_id, auth='physician')

        return Response({'token': token}, status=HTTP_200_OK)
    except:
        return Response({'message': 'token_expire'}, status=HTTP_401_UNAUTHORIZED)




@swagger_auto_schema(
	operation_description='Link between patient and physician.',
	method='post',
	responses={
		HTTP_201_CREATED: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def add_patient(request):
    token = request.META.get('HTTP_TOKEN')
    d_id = get_id(token)
    code = request.data['code']

    # TODO ---- change to setting code generation number
    if code > 1000:
        p_id = code - 1000

    else:
        return Response(status=HTTP_400_BAD_REQUEST)

    d_p_relation = DPRelation()
    d_p_relation.p = p_id
    d_p_relation.d = d_id
    d_p_relation.add_time = datetime.datetime.now()
    d_p_relation.save()

    return Response(status=HTTP_201_CREATED)


@swagger_auto_schema(
	operation_description='Get infos on patients.',
	method='get',
	responses={
		HTTP_201_CREATED: 'Success',
		HTTP_400_BAD_REQUEST: 'Bad request.',
	},
)
@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def get_main(request):
    token = request.META.get('HTTP_TOKEN')
    d_id = get_id(token)

    p_id_obj = DPRelation.objects.filter(d=d_id).values_list('p')
    p_id_lst = [i[0] for i in p_id_obj]

    main_lst = []
    for p_id in p_id_lst:
        main_dic = {}
        last_seen_cnt = DUpdate.objects.select_related('relation_id').filter(Q(relation__d=d_id) &
                                                                             Q(relation__p=p_id) &
                                                                             Q(type__exact=1) &
                                                                             Q(seen=0)).count()
        if last_seen_cnt > 0:
            main_dic['news'] = 1
        else:
            main_dic['news'] = 0

        predict_lst = PDailyPredict.objects.select_related('p_daily__p').filter(p_daily__p__p_id=p_id).\
            order_by('-p_daily__p_daily_time').values_list('oxygen', 'icu')

        if len(predict_lst) > 1:
            this_oxygen = predict_lst[0][0]
            this_icu = predict_lst[0][1]

            previous_oxygen = predict_lst[1][0]
            previous_icu = predict_lst[1][1]

            if this_oxygen > previous_oxygen:
                main_dic['oxygen_change'] = 1
            elif this_oxygen < previous_oxygen:
                main_dic['oxygen_change'] = -1
            else:
                main_dic['oxygen_change'] = 0

            if this_icu > previous_icu:
                main_dic['icu_change'] = 1
            elif this_icu < previous_icu:
                main_dic['icu_change'] = -1
            else:
                main_dic['icu_change'] = 0
        else:
            main_dic['oxygen_change'] = 0
            main_dic['icu_change'] = 0

        if len(predict_lst) > 0:
            main_dic['oxygen'] = predict_lst[0][0]
            main_dic['icu'] = predict_lst[0][1]
        else:
            main_dic['oxygen'] = None
            main_dic['icu'] = None

        p_info = PInfo.objects.get(p=p_id)
        born = datetime.datetime.strptime(p_info.birth, "%Y-%m-%d")
        today = datetime.datetime.today()

        main_dic['name'] = p_info.name
        main_dic['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

        oxygen_obj = DOxygen.objects.select_related('relation').filter(Q(relation__p=p_id) &
                                                                       Q(oxygen_end__isnull=True))
        if oxygen_obj:
            main_dic['oxygen_supply'] = 1
        else:
            main_dic['oxygen_supply'] = 0

        main_lst.append(main_dic)

    return Response(main_lst, status=HTTP_200_OK)
