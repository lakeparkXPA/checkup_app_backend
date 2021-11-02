from django.db.models import Q
from django.core.validators import validate_email

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from checkup_backend.settings import ALGORITHM, SECRET_KEY, FIREBASE_KEY, PATIENT_CODE
from checkup_backend.permissions import PhysicianAuthenticated
from checkup_backend import error_collection

from physician.serializers import *
from patient.models import DLogin, DPRelation, DUpdate, PDailyPredict
from patient.serializers import FixedGet, DailyGet

from tools import make_token, get_id

import jwt
import datetime
import requests
import json


@swagger_auto_schema(
	operation_description='Register physician account.',
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
		HTTP_201_CREATED: '\n\n> **회원가입, 토큰 반환**\n\n```\n{\n\n\t"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0",\n\t"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0"\n\n}\n\n```',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_MISSING.as_md() +
                              error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
                              error_collection.RAISE_400_EMAIL_EXIST.as_md() +
                              error_collection.RAISE_400_PASSWORD_NOT_SAME.as_md(),
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
            login_obj = DLogin.objects.filter(email=email)
            token = PhysicianLogin(login_obj, many=True).data[0]
            d_user = DLogin.objects.get(email=email)
            d_user.refresh_token = token['refresh_token'].decode()
            d_user.save()
            return Response(token, status=HTTP_201_CREATED)
        else:
            return Response(d_serial.errors, status=HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


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
		HTTP_200_OK: 'registrable: True/False',
        HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_EMAIL_MISSING.as_md() +
            error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
            error_collection.RAISE_400_EMAIL_EXIST.as_md(),
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
            validate_email(email)
        except:
            raise ValueError('email_format')
        try:
            id_cnt = DLogin.objects.get(email=email)
            res = Response({"registrable": False}, status=HTTP_200_OK)
            return res
        except DLogin.DoesNotExist:
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
        HTTP_200_OK: '\n\n> **로그인, 토큰 반환**\n\n```\n{\n\n\t"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0",\n\t"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRoIjoicGF0aWVudCIsImlkIjoxOSwiZXhwIjoxNjMzOTY4MTYxfQ.UqAuOEklo8cxTgJtd8nPJSlFgmcZB5Dvd27YGemrgb0"\n\n}\n\n```',
        HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
                              error_collection.RAISE_400_WRONG_PASSWORD.as_md() +
                              error_collection.RAISE_400_WRONG_EMAIL.as_md(),
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
                    try:
                        push_token = request.data['push_token']
                        if push_token:
                            d_user = DLogin.objects.get(email=email)
                            d_user.push_token = push_token
                            d_user.alert = 0
                            d_user.save()
                    except:
                        pass

                    token = PhysicianLogin(login_obj, many=True).data[0]

                    d_user = DLogin.objects.get(email=email)
                    d_user.refresh_token = token['refresh_token'].decode()
                    d_user.save()
                    return Response(token, status=HTTP_200_OK)

            except DLogin.DoesNotExist:
                raise ValueError('wrong_email')
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Edit account. Select one mode (email, password, alert)',
	method='put',
	request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
            'mode': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Mode (email, password, alert)'),
        	'email': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Email'),
        	'password': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Password'),
            'alert': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Name'),
    	},
	),
	responses={
		HTTP_201_CREATED: 'Edited.',
		HTTP_400_BAD_REQUEST: error_collection.RAISE_400_EMAIL_MISSING.as_md() +
        error_collection.RAISE_400_EMAIL_FORMAT_INVALID.as_md() +
        error_collection.RAISE_400_EMAIL_EXIST.as_md() +
        error_collection.RAISE_400_WRONG_MODE.as_md(),
	},
)
@api_view(['PUT'])
@permission_classes((PhysicianAuthenticated,))
def physician_edit(request):
    d_id = get_id(request)

    mode = request.data['mode']
    d_login = DLogin.objects.get(d_id=d_id)
    try:
        if mode == 'email':
            email = request.data['email']
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
            d_login.email = email
        elif mode == 'password':
            password = request.data['password']
            d_login.password = password
        elif mode == 'alert':
            alert = int(request.data['alert'])
            if alert >= 0 & alert < 3:
                d_login.alert = alert
        else:
            raise ValueError('wrong_mode')

        d_login.save()

        return Response(status=HTTP_200_OK)
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
        d_id = client_decoded['id']
        d_user = PLogin.objects.get(d_id=d_id)
        db_refresh_token = d_user.refresh_token
        db_decoded = jwt.decode(db_refresh_token, SECRET_KEY, ALGORITHM)
        if db_decoded['auth'] and client_decoded['auth'] == 'refresh' and client_decoded == db_decoded:
            login_obj = DLogin.objects.filter(d_id=d_id)
            token = PhysicianLogin(login_obj, many=True).data[0]

            d_user.refresh_token = token['refresh_token'].decode()
            d_user.save()

            return Response(token, status=HTTP_201_CREATED)
        else:
            return Response({'message': 'wrong_refresh_token'}, status=HTTP_401_UNAUTHORIZED)
    except:
        return Response({'message': 'refresh_token_expire'}, status=HTTP_401_UNAUTHORIZED)




@swagger_auto_schema(
	operation_description='Link between patient and physician.',
	method='post',
    request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'code': openapi.Schema(
					type=openapi.TYPE_NUMBER,
					description='Code'),
    	},
		required=['code'],
	),
	responses={
		HTTP_201_CREATED: 'Success',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_WRONG_CODE.as_md() +
            error_collection.RAISE_400_RELATION_EXISTS.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def add_patient(request):
    d_id = get_id(request)
    code = request.data['code']
    try:
        if code > PATIENT_CODE:
            p_id = code - PATIENT_CODE
        else:
            raise ValueError('wrong_code')


        dp_relation = DPRelation.objects.filter(p=p_id, d=d_id)
        if dp_relation:
            raise ValueError('relation_exists')



        p_obj = PLogin.objects.get(p_id=p_id)
        p_push = p_obj.push_token
        p_locale = p_obj.locale

        d_p_relation = DPRelation()
        d_p_relation.p = p_obj
        d_p_relation.d = DLogin.objects.get(d_id=d_id)
        d_p_relation.discharged = 0
        d_p_relation.add_time = datetime.datetime.now()
        d_p_relation.save()

        d_name = DLogin.objects.get(d_id=d_id).name

        if p_push:
            if p_locale == 'kr':
                title = "담당 의료진이 추가되었습니다."
                body = "담당 의료진 " + d_name + " 이 회원님을 진료 환자 목록에 추가했습니다. 체크업 기록을 진행해주세요!"
            elif p_locale == 'ja':
                title = ""
                body = ""
            elif p_locale == 'id':
                title = 'Tenaga medis telah ditambahkan'
                body = 'Anda telah ditambahkan di dalam daftar pasien tenaga medis Dokter ' + d_name + \
                       '. Tuliskan riwayat CheckUp.'
            else:
                title = "Medical Team member added."
                body = "The medical team member " + d_name + " has added you to the patient list. " \
                                                             "Please check your status with a new check-up!"

            url = 'https://fcm.googleapis.com/fcm/send'

            headers = {
                'Authorization': 'key=' + FIREBASE_KEY,
                'Content-Type': 'application/json; UTF-8',
            }
            contents = {
                'registration_ids': [p_push],
                'notification': {
                    'title': title,
                    'body': body
                }
            }
            requests.post(url, data=json.dumps(contents), headers=headers)

        return Response(status=HTTP_201_CREATED)

    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)



@swagger_auto_schema(
	operation_description='Get basic info on patients.',
	method='get',
	responses={
		HTTP_200_OK: '\n\n> **환자 목록 및 기본 정보 반환 (반환 예 하단 참고)**\n\n```\n[\n\t{\n\t\t"p_id": 19,\n\t\t"news": 0,\n\t\t"oxygen_change": 0,\n\t\t"icu_change": 0,\n\t\t"oxygen": 0.44002,\n\t\t"icu": 0.494376,\n\t\t"name": null,\n\t\t"age": 28\n\t},\n\t{\n\t\t"p_id": 19,\n\t\t"news": 0,\n\t\t"oxygen_change": 0,\n\t\t"icu_change": 0,\n\t\t"oxygen": 0.44002,\n\t\t"icu": 0.494376,\n\t\t"name": null,\n\t\t"age": 28,\n\t\t"sex":0,\n\t\t"discharged":1,\n\t\t"dyspnea":0\n\t},\n...]\n\n```',
		HTTP_401_UNAUTHORIZED:
            error_collection.RAISE_401_NO_TOKEN.as_md(),
	},
)
@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def get_main(request):
    d_id = get_id(request)

    p_id_obj = DPRelation.objects.filter(Q(d=d_id) & Q(discharged=0)).values_list('p')
    p_id_lst = [i[0] for i in p_id_obj]

    main_lst = []
    for p_id in p_id_lst:
        main_dic = {"p_id": p_id}
        last_seen_cnt = DUpdate.objects.select_related('relation_id').filter(Q(relation__d=d_id) &
                                                                             Q(relation__p=p_id) &
                                                                             Q(type__exact=1) &
                                                                             Q(seen=0)).count()
        if last_seen_cnt > 0:
            main_dic['news'] = 1
        else:
            main_dic['news'] = 0

        predict_lst = PDailyPredict.objects.select_related('p_daily__p').filter(p_daily__p__p_id=p_id).\
            order_by('-p_daily__p_daily_time').values_list('oxygen', 'icu', 'p_daily__p')

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
        born = p_info.birth
        today = datetime.datetime.today()

        main_dic['name'] = p_info.name
        main_dic['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        main_dic['sex'] = p_info.sex

        main_dic['discharged'] = 1 if DPRelation.objects.filter(p=p_id, discharged=1) else 0
        main_dic['dyspnea'] = PDailySymptom.objects.select_related('p_daily__p').filter(p_daily__p=p_id).\
            latest('p_daily').dyspnea


        # oxygen_obj = DOxygen.objects.select_related('relation').filter(Q(relation__p=p_id) &
        #                                                                Q(oxygen_end__isnull=True))
        # if oxygen_obj:
        #     main_dic['oxygen_supply'] = 1
        # else:
        #     main_dic['oxygen_supply'] = 0

        main_lst.append(main_dic)

    return Response(main_lst, status=HTTP_200_OK)


@swagger_auto_schema(
	operation_description='Get fixed variables on patients.',
	method='get',
    manual_parameters=[
            openapi.Parameter(
                'pid',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Patient ID'
            ),
    ],
	responses={
	    HTTP_200_OK: '\n\n> **환자 고정 정보 반환 (반환 예 하단 참고)**\n\n```\n{\n\t"p_fixed_id": 7,\n\t"smoking": 1,\n\t"height": 182,\n\t"weight": 102,\n\t"adl": 0,\n\t"p_id": 19,\n\t"chronic_cardiac_disease": 1,\n\t"chronic_neurologic_disorder": 1,\n\t"copd": 1,\n\t"asthma": 1,\n\t"chronic_liver_disease": 1,\n\t"hiv": 1,\n\t"autoimmune_disease": 1,\n\t"dm": 0,\n\t"hypertension": 0,\n\t"ckd": 0,\n\t"cancer": 0,\n\t"heart_failure": 0,\n\t"dementia": 0,\n\t"chronic_hematologic_disorder": 0,\n\t"transplantation": 1,\n\t"immunosuppress_agent": 1,\n\t"chemotherapy": 0,\n\t"pregnancy": 0,\n\t"name": null,\n\t"birth": "1992-12-25",\n\t"sex": 0,\n\t"age": 28\n}\n\n```',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_RELATION_NONEXISTENT.as_md() +
            error_collection.RAISE_400_PID_NONEXISTENT.as_md(),
	},
)
@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def get_fixed(request):
    d_id = get_id(request)
    p_id = int(request.GET.get('pid'))
    try:
        if p_id:
            try:
                dp_relation = DPRelation.objects.get(p=p_id ,d=d_id)

                fixed = PFixed.objects.filter(p=p_id)
                return_dic = FixedGet(fixed, many=True).data[0]

                p_info = PInfo.objects.get(p=p_id)
                born = p_info.birth
                today = datetime.datetime.today()

                return_dic['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

                return Response(return_dic, status=HTTP_200_OK)

            except DPRelation.DoesNotExist:
                raise ValueError('relation_nonexistent')
        else:
            raise ValueError('p_id_nonexistent')
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Get patients detail info and daily variable.',
	method='get',
    manual_parameters=[
            openapi.Parameter(
                'pid',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Patient ID'
            ),
    ],
	responses={
	    HTTP_200_OK: '\n\n> **환자 데일리 정보 반환 (반환 예 하단 참고)**\n\n```\n{\n\t"discharged": 0,\n\t"p_id": 19,\n\t"name": null,\n\t"birth": "1992-12-25",\n\t"sex": 0,\n\t"age": 28,\n\t"receives_push": 0,\n\t"daily": [\n\t\t{\n\t\t\t"p_daily_id": 6,\n\t\t\t"p_daily_time": "2021-09-15T07:55:47Z",\n\t\t\t"latitude": 0,\n\t\t\t"longitude": 0,\n\t\t\t"p_id": 19,\n\t\t\t"hemoptysis": 0,\n\t\t\t"dyspnea": 0,\n\t\t\t"chest_pain": 0,\n\t\t\t"cough": 0,\n\t\t\t"sputum": 0,\n\t\t\t"rhinorrhea": 0,\n\t\t\t"sore_throat": 0,\n\t\t\t"anosmia": 0,\n\t\t\t"myalgia": 0,\n\t\t\t"arthralgia": 0,\n\t\t\t"fatigue": 0,\n\t\t\t"headache": 0,\n\t\t\t"diarrhea": 0,\n\t\t\t"nausea_vomiting": 0,\n\t\t\t"chill": 0,\n\t\t\t"antipyretics": 1,\n\t\t\t"temp_capable": 1,\n\t\t\t"temp": 37.5,\n\t\t\t"prediction_result": 44,\n\t\t\t"prediction_explaination": "{\"ml_class\": 1, \"ml_probability\": 0.440020352602005, \"stat_class\": 1, \"stat_probability\": 1.3409791840000034, \"status\": \"ok\", \"icu\": 0.4943764805793762}",\n\t\t\t"oxygen": 0.44002,\n\t\t\t"icu": 0.494376\n\t\t},\n\t\t...\n\t]\n}\n\n```',
        HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_PID_MISSING.as_md() +
            error_collection.RAISE_400_RELATION_NONEXISTENT.as_md(),
	},
)
@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def physician_patient(request):
    d_id = get_id(request)
    p_id = request.GET.get('pid')

    if p_id:
        dp_relation_filter = DPRelation.objects.filter(d=d_id, p=p_id)
        general = DPfixed(dp_relation_filter, many=True).data[0]

        dp_relation = DPRelation.objects.get(d=d_id, p=p_id)

        if not dp_relation:
            return Response({"code": "relation_nonexistent"}, status=HTTP_400_BAD_REQUEST)

        DUpdate.objects.filter(relation_id=dp_relation.relation_id).update(seen=1)


        # d_oxygen = DOxygen.objects.filter(relation_id=dp_relation.relation_id).values('oxygen_start')
        # if d_oxygen:
        #     general['oxygen_supply'] = 1
        #     general['oxygen_start'] = d_oxygen[0]['oxygen_start']
        # else:
        #     general['oxygen_supply'] = 0

        p_push = PLogin.objects.get(p_id=p_id).push_token
        if p_push:
            general['receives_push'] = 1
        else:
            general['receives_push'] = 0

        daily = PDaily.objects.filter(p=p_id).order_by('-p_daily_id')
        daily_lst = DailyGet(daily, many=True).data
        for row in daily_lst:
            row['prediction_result'] = round(row['prediction_result'], 2)

        general['daily'] = daily_lst
        general['p_id'] = p_id

        return Response(general, status=HTTP_200_OK)
    else:
        return Response({'code': 'p_id_missing'}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Get patients and physician update notice list.',
	method='get',
	responses={
	    HTTP_200_OK: '\n\n> **환자 업데이트 정보 반환 (반환 예 하단 참고)**\n\n```\n{\n\t[\n\t\t"p_id": 19,\n\t\t"name": "docl",\n\t\t"type": 1,\n\t\t"seen": 0,\n\t\t"time": "2021-01-01 13:49:41",\n\t\t"oxygen_delta": 0.5129,\n\t\t"icu_delta": 0.49123,\n\t],\n\t...\n}\n\n```',
	},
)
@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def get_updates(request):
    d_id = get_id(request)

    result = []
    relation_lst = DPRelation.objects.filter(d=d_id).values_list('relation_id', flat=True)
    update_lst = DUpdate.objects.filter(relation_id__in=relation_lst).order_by('-d_update_id').\
                     values('relation_id', 'type', 'seen', 'data', 'recorded_time')[:300]

    for row in update_lst:
        update_dic = {}
        update_dic['p_id'] = DPRelation.objects.get(relation_id=row['relation_id']).p.p_id
        update_dic['name'] = PInfo.objects.get(p=update_dic['p_id']).name
        update_dic['type'] = row['type']
        update_dic['seen'] = row['seen']
        update_dic['time'] = row['recorded_time']
        if row['type'] == 1:
            data_decode = json.loads(row['data'])
            update_dic['oxygen_delta'] = float(data_decode['oxygen'])
            update_dic['icu_delta'] = float(data_decode['icu'])

        result.append(update_dic)

    return Response(result, status=HTTP_200_OK)


@swagger_auto_schema(
	operation_description='Send push alert to patient to do check up.',
	method='post',
    request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'pid': openapi.Schema(
					type=openapi.TYPE_NUMBER,
					description='Patient Id'),
    	},
		required=['pid'],
	),
	responses={
		HTTP_201_CREATED: 'Success',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_PID_MISSING.as_md() +
            error_collection.RAISE_400_PATIENT_PUSH_TOKEN_NULL.as_md() +
            error_collection.RAISE_400_RELATION_NONEXISTENT.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def send_alert(request):
    d_id = get_id(request)
    p_id = request.data['pid']
    try:
        try:

            if not p_id:
                raise ValueError("p_id_missing")

            dp_relation = DPRelation.objects.get(d=d_id, p=p_id)
            p_obj = PLogin.objects.get(p_id=p_id)
            p_push = p_obj.push_token
            p_locale = p_obj.locale
            if p_push:
                if p_locale == 'kr':
                    title = "기록을 작성해주세요"
                    body = "의료진이 새로운 기록을 요청했습니다. 체크업 기록을 진행해주세요!"
                elif p_locale == 'ja':
                    title = "記録を作成してください"
                    body = "医療陣があなたの新しい記録を要請しました。チェックアップ記録を進めてください！"
                elif p_locale == 'id':
                    title = 'Tuliskan gejalan anda'
                    body = 'Tenaga medis meminta gejala anda untuk dituliskan. Tuliskan riwayat anda di CheckUp!'
                else:
                    title = "A new request"
                    body = "The medical team is wondering about your status. Please check your status with a new check-up!"

                url = 'https://fcm.googleapis.com/fcm/send'

                headers = {
                    'Authorization': 'key=' + FIREBASE_KEY,
                    'Content-Type': 'application/json; UTF-8',
                }
                contents = {
                    'registration_ids': [p_push],
                    'notification': {
                        'title': title,
                        'body': body
                    }
                }
                requests.post(url, data=json.dumps(contents), headers=headers)
                return Response(status=HTTP_200_OK)
            else:
                raise ValueError('patient_push_token_null')
        except DPRelation.DoesNotExist:
            raise ValueError('relation_nonexistent')
    except Exception as e:
        return Response({"code": str(e)}, status=HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
	operation_description='Discharge patient.',
	method='post',
    request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'pid': openapi.Schema(
					type=openapi.TYPE_NUMBER,
					description='patient id'),
            'reverse': openapi.Schema(
					type=openapi.TYPE_NUMBER,
					description='reverse the discharge or not'),
            'worsened': openapi.Schema(
					type=openapi.TYPE_BOOLEAN,
					description='Worsened or not'),
            'cause': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Cause of discharge'),
    	},
		required=['pid', 'reverse'],
	),
	responses={
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_PID_MISSING.as_md() +
            error_collection.RAISE_400_RELATION_NONEXISTENT.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def physician_discharge(request):
    d_id = get_id(request)
    p_id = request.data['pid']
    reverse = request.data['reverse']

    if not p_id:
        return Response({"code": "p_id_missing"}, status=HTTP_400_BAD_REQUEST)

    dp_relation = DPRelation.objects.get(d=d_id, p=p_id)

    if not dp_relation:
        return Response({"code": "relation_nonexistent"}, status=HTTP_400_BAD_REQUEST)

    d_update = DUpdate(relation=dp_relation)

    if int(reverse) > 0:
        dp_relation.discharged = 0

        d_update.type = 0

    else:
        dp_relation.discharged = 1
        try:
            worsened = request.data['worsened']
            dp_relation.worsened = int(worsened)
        except:
            pass
        try:
            cause = request.data['cause']
            dp_relation.cause = cause
        except:
            pass

        d_update.type = 2
    d_update.recorded_time = datetime.datetime.now()
    d_update.seen = 0
    d_update.save()
    dp_relation.save()

    return Response(status=HTTP_200_OK)



@swagger_auto_schema(
	operation_description='Set patient oxygen.',
	method='post',
    request_body=openapi.Schema(
    	type=openapi.TYPE_OBJECT,
    	properties={
        	'pid': openapi.Schema(
					type=openapi.TYPE_NUMBER,
					description='patient id'),
            'start': openapi.Schema(
					type=openapi.TYPE_BOOLEAN,
					description='Start or ended'),
    	},
		required=['pid', 'start'],
	),
	responses={
		HTTP_200_OK: 'Success',
		HTTP_400_BAD_REQUEST:
            error_collection.RAISE_400_PID_MISSING.as_md() +
            error_collection.RAISE_400_RELATION_NONEXISTENT.as_md() +
            error_collection.RAISE_400_OXYGEN_RECORD_NONEXISTENT.as_md(),
	},
)
@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def set_oxygen(request):
    d_id = get_id(request)
    p_id = request.data['pid']
    start = request.data['start']

    if not p_id:
        return Response({"code": "p_id_missing"}, status=HTTP_400_BAD_REQUEST)

    dp_relation = DPRelation.objects.get(d=d_id, p=p_id)

    if not dp_relation:
        return Response({"code": "relation_nonexistent"}, status=HTTP_400_BAD_REQUEST)


    if start:
        d_oxygen = DOxygen(relation=dp_relation)
        d_oxygen.oxygen_start = datetime.datetime.now()
    else:
        try:
            d_oxygen = DOxygen.objects.get(relation=dp_relation.relation_id, oxygen_end__isnull=True)
            d_oxygen.oxygen_end = datetime.datetime.now()
        except:
            return Response({"code": "oxygen_record_nonexistent"}, status=HTTP_400_BAD_REQUEST)

    d_oxygen.save()

    return Response(status=HTTP_200_OK)
