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
from patient.serializers import FixedGet, DailyGet

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

            except DLogin.DoesNotExist:
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
    d_id = get_id(request)
    code = request.data['code']
    try:
        # TODO ---- change to setting code generation number
        if code > 1001:
            p_id = code - 1001
        else:
            raise ValueError('code_incorrect')

        try:
            dp_relation = DPRelation.objects.get(p=p_id, d=d_id)
            raise ValueError('relation_exists')
        except DPRelation.DoesNotExist:
            pass
        d_p_relation = DPRelation()
        d_p_relation.p = p_id
        d_p_relation.d = d_id
        d_p_relation.discharged = 0
        d_p_relation.add_time = datetime.datetime.now()
        d_p_relation.save()

        p_obj = PLogin.objects.get(p_id=p_id)
        p_push = p_obj.push_token
        p_locale = p_obj.locale

        d_name = DLogin.objects.get(d_id=d_id).name

        if p_push:
            if p_locale == 'kr':
                title = "담당 의료진이 추가되었습니다."
                body = "담당 의료진 " + d_name + " 이 회원님을 진료 환자 목록에 추가했습니다. 체크업 기록을 진행해주세요!"
            elif p_locale == 'ja':
                title = ""
                body = ""
            elif p_locale == 'in':
                title = ''
                body = ''
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
    d_id = get_id(request)

    p_id_obj = DPRelation.objects.filter(Q(d=d_id) & Q(discharged=0)).values_list('p')
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

        # oxygen_obj = DOxygen.objects.select_related('relation').filter(Q(relation__p=p_id) &
        #                                                                Q(oxygen_end__isnull=True))
        # if oxygen_obj:
        #     main_dic['oxygen_supply'] = 1
        # else:
        #     main_dic['oxygen_supply'] = 0

        main_lst.append(main_dic)

    return Response(main_lst, status=HTTP_200_OK)



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
                born = datetime.datetime.strptime(p_info.birth, "%Y-%m-%d")
                today = datetime.datetime.today()

                return_dic['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

                return Response(return_dic, status=HTTP_200_OK)

            except DPRelation.DoesNotExist:
                raise ValueError('relation_nonexistent')
        else:
            raise ValueError('p_id_nonexistent')
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)



@api_view(['PUT'])
@permission_classes((PhysicianAuthenticated,))
def physician_edit(request):
    d_id = get_id(request)

    mode = request.data['mode']
    d_login = DLogin.objects.get(d_id=d_id)
    if mode == 'email':
        email = request.data['email']
        d_login.email = email
    elif mode == 'password':
        password = request.data['password']
        d_login.password = password
    elif mode == 'alert':
        alert = int(request.data['alert'])
        if alert >= 0 & alert < 3:
            d_login.alert = alert
    else:
        return Response({"message": 'wrong_mode'}, status=HTTP_400_BAD_REQUEST)

    d_login.save()

    return Response(status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def physician_discharge(request):
    d_id = get_id(request)
    p_id = request.data['pid']
    reverse = request.data['reverse']

    dp_relation = DPRelation.objects.get(d=d_id, p=p_id)
    d_update = DUpdate(relation=dp_relation)
    if int(reverse) > 0:
        dp_relation.discharged = 0

        d_update.type = 1

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

    d_update.seen = 0
    d_update.save()
    dp_relation.save()

    return Response(status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def physician_patient(request):
    d_id = get_id(request)
    p_id = request.GET.get('pid')

    if p_id:
        dp_relation_filter = DPRelation.objects.filter(d=d_id, p=p_id)
        general = DPfixed(dp_relation_filter, many=True).data[0]

        dp_relation = DPRelation.objects.get(d=d_id, p=p_id)
        d_update = DUpdate(relation_id=dp_relation)
        d_update.seen = 1
        d_update.save()

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

        return Response(general, status=HTTP_200_OK)
    else:
        return Response({'code': 'patient_id_missing'}, status=HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((PhysicianAuthenticated,))
def get_updates(request):
    d_id = get_id(request)

    result = []
    relation_lst = DPRelation.objects.filter(d=d_id).values_list('relation_id', flat=True)
    update_lst = DUpdate.objects.filter(relation_id__in=relation_lst).order_by('-d_update_id').\
                     values('relation_id', 'type', 'seen','data', 'recorded_time')[:300]

    for row in update_lst:
        update_dic = {}
        update_dic['patient_no'] = DPRelation.objects.get(relation_id=row['relation_id']).p
        update_dic['name'] = PInfo.objects.get(p=update_dic['patient_no']).name
        update_dic['type'] = row['type']
        update_dic['seen'] = row['seen']
        update_dic['time'] = row['recorded_time']
        if row['type'] == 1:
            data_decode = json.loads(row['data'])
            update_dic['oxygen_delta'] = float(data_decode['oxygen'])
            update_dic['icu_delta'] = float(data_decode['icu'])

        result.append(update_dic)

    return Response(result, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes((PhysicianAuthenticated,))
def send_alert(request):
    d_id = get_id(request)
    p_id = request.data['pid']
    try:
        try:
            dp_relation = DPRelation.objects.get(Q(p=p_id) & Q(d=d_id))
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
                elif p_locale == 'in':
                    title = ''
                    body = ''
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
