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

from patient.serializers import *
from patient.models import PLogin, PInfo, PFixed, PFixedUnique, PFixedCondition, PDaily, PDailyPredict, PDailySymptom, \
    PDailyTemperature, DPRelation, DUpdate

import jwt
import datetime
import requests
import json

# TODO ---- 회원탈퇴 api
# TODO ---- get daily update,
# TODO ---- 의료진 환자 추가 시 push 알림

def make_token(token_id):
    payload = {}
    payload['auth'] = 'patient'
    payload['id'] = token_id
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=300)

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)


def get_id(token):
    decoded_token = jwt.decode(token, SECRET_KEY, ALGORITHM)
    return decoded_token['id']


def bool_dic(data, data_lst):
    data_dic = {}
    for d in data_lst:
        if d in data:
            data_dic[d] = 1
        else:
            data_dic[d] = 0
    return data_dic



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

                    return Response(token, status=HTTP_200_OK)

            except PLogin.DoesNotExist:
                raise ValueError('wrong_email')
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


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

        return Response({'token': token}, status=HTTP_200_OK)
    except:
        return Response({'message': 'token_expire'}, status=HTTP_401_UNAUTHORIZED)


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

        return Response(status=HTTP_201_CREATED)
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


class Fixed(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [PatientAuthenticated]

    @swagger_auto_schema(
        operation_description='Getting fixed data.',
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


@api_view(['POST', 'PUT'])
@permission_classes((PatientAuthenticated,))
def set_fixed(request):

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

    if request.method == 'POST':
        try:
            id_cnt = PFixed.objects.get(p_id=p_id)
            return Response({'message': 'fixed_exist'}, status=HTTP_405_METHOD_NOT_ALLOWED)
        except PFixed.DoesNotExist:
            pass
        p_fixed = PFixed(p_id=p_id)

        p_fixed.save()
        p_detail = PInfo(p=p_user)

        res = Response(status=HTTP_201_CREATED)

    else:
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


@api_view(['POST'])
@permission_classes((PatientAuthenticated,))
def set_daily(request):
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
    p_fixed_condition = list(PFixedCondition.objects.filter(p_fixed_id=p_fixed).\
                             values('chronic_cardiac_disease', 'chronic_neurologic_disorder', 'copd', 'asthma',
                                    'chronic_liver_disease', 'hiv', 'autoimmune_disease', 'dm', 'hypertension', 'ckd',
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

    prediction = json.loads(requests.get("https://model.docl.org/predict", data).json())
    prediction_icu = json.loads(requests.get("https://model.docl.org/predict_icu", data).json())
    prediction['icu'] = prediction_icu['probability']

    p_daily = PDaily(p=p_id)
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
    p_daily_predict.save()

    previous_id_lst = list(PDaily.objects.filter(p_id=p_id).order_by('-p_daily_time').values('p_daily_id'))

    update_data = {}
    if len(previous_id_lst) > 1:
        previous_icu = PDailyPredict.objects.get(p_daily_id=previous_id_lst[1]).prediction_explaination
        previous_icu_decode = json.loads(previous_icu)
        update_data['oxygen'] = prediction['ml_probability'] - previous_icu_decode['ml_probability']
        update_data['icu'] = prediction['icu'] - previous_icu_decode['ice']
    else:
        update_data['oxygen'] = 0
        update_data['icu'] = 0

    doc_lst = DPRelation.objects.select_related('d').select_related('p').filter(Q(p=p_id) & Q(discharged=0)).\
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
            if round(100*update_data['oxygen']) < 0:
                pushbody += "improved by " + str(round((-100) * update_data['oxygen'])) + "% and "
            elif round(100*update_data['oxygen']) > 0:
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
                'Authorization': 'key='+FIREBASE_KEY,
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


@api_view(['POST'])
@permission_classes((PatientAuthenticated,))
def get_fixed(request):
    token = request.META.get('HTTP_TOKEN')
    p_id = get_id(token)
    fixed = PFixed.objects.prefetch_related('pfixedcondition_set').prefetch_related('pfixedunique_set').filter(p=p_id)
    fixed_val = fixed.values('p_fixed_id', 'p', 'smoking', 'height', 'weight', 'adl',
                             chronic_cardiac_disease=F('pfixedcondition__chronic_cardiac_disease'),
                             chronic_neurologic_disorder=F('pfixedcondition__chronic_neurologic_disorder'),
                             copd=F('pfixedcondition__copd'),
                             asthma=F('pfixedcondition__asthma'),
                             chronic_liver_disease=F('pfixedcondition__chronic_liver_disease'),
                             hiv=F('pfixedcondition__hiv'),
                             autoimmune_disease=F('pfixedcondition__autoimmune_disease'),
                             dm=F('pfixedcondition__dm'),
                             hypertension=F('pfixedcondition__hypertension'),
                             ckd=F('pfixedcondition__ckd'),
                             cancer=F('pfixedcondition__cancer'),
                             heart_failure=F('pfixedcondition__heart_failure'),
                             dementia=F('pfixedcondition__dementia'),
                             chronic_hematologic_disorder=F('pfixedcondition__chronic_hematologic_disorder'),
                             transplantation=F('pfixedunique__transplantation'),
                             immunosuppress_agent=F('pfixedunique__immunosuppress_agent'),
                             chemotherapy=F('pfixedunique__chemotherapy'),
                             pregnancy=F('pfixedunique__pregnancy')
                             )
    return_dic = dict(list(PInfo.objects.filter(p=19).values('name', 'birth', 'sex'))[0])
    return_dic.update(dict(list(fixed_val)[0]))

    return Response(return_dic, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes((PatientAuthenticated,))
def get_daily(request):
    token = request.META.get('HTTP_TOKEN')
    pagenation = request.data['pagenation']
    sort = request.data['sort']
    # 최신/오래, 체온
    start_date = request.data['start_date']
    end_date = request.data['end_date']
    #날짜
    p_id = get_id(token)

    daily = PDaily.objects.prefetch_related('pdailysymptom_set', 'pdailypredict_set', 'pdailytemperature_set').\
        filter(p=p_id).order_by('-p_daily_id')
    daily_lst = daily.values('p_daily_id', 'p', 'p_daily_time', 'latitude', 'longitude',
                             prediction_result=F('pdailypredict__prediction_result'),
                             prediction_explaination=F('pdailypredict__prediction_explaination'),
                             hemoptysis=F('pdailysymptom__hemoptysis'),
                             dyspnea=F('pdailysymptom__dyspnea'),
                             chest_pain=F('pdailysymptom__chest_pain'),
                             cough=F('pdailysymptom__cough'),
                             sputum=F('pdailysymptom__sputum'),
                             rhinorrhea=F('pdailysymptom__rhinorrhea'),
                             sore_throat=F('pdailysymptom__sore_throat'),
                             anosmia=F('pdailysymptom__anosmia'),
                             myalgia=F('pdailysymptom__myalgia'),
                             arthralgia=F('pdailysymptom__arthralgia'),
                             fatigue=F('pdailysymptom__fatigue'),
                             headache=F('pdailysymptom__headache'),
                             diarrhea=F('pdailysymptom__diarrhea'),
                             nausea_vomiting=F('pdailysymptom__nausea_vomiting'),
                             chill=F('pdailysymptom__chill'),
                             antipyretics=F('pdailytemperature__antipyretics'),
                             temp_capable=F('pdailytemperature__temp_capable'),
                             temp=F('pdailytemperature__temp'),
                             )
    return Response(daily_lst, status=HTTP_200_OK)


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

    return Response({'code': p_id + 1000}, status=HTTP_201_CREATED)


