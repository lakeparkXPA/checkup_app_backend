from django.db.models import Q, F
from django.core.validators import validate_email

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from checkup_backend.settings import ALGORITHM, SECRET_KEY
from checkup_backend.permissions import PatientAuthenticated

from patient.models import PLogin, PInfo, PFixed, PFixedUnique, PFixedCondition

import jwt
import datetime


def make_token(token_id):
    payload = {}
    payload['auth'] = 'patient'
    payload['id'] = token_id
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=300)

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


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_register(request):
    email = request.data['email']
    password1 = request.data['password1']
    password2 = request.data['password2']
    agreed = request.data['agreed']

    name = request.data['name']
    birth = request.data['birth']
    sex = request.data['sex']
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
        p_detail.birth = birth
        p_detail.sex = sex
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


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def patient_login(request):
    email = request.data['email']
    password = request.data['password']
    login_obj = PLogin.objects.get(email=email)
    try:
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        else:
            try:
                db_pass = login_obj.password

                if db_pass != password:
                    raise ValueError('wrong_password')
                else:
                    token = make_token(login_obj.p_id)

                    return Response({'token': token}, status=HTTP_200_OK)

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
    birth = request.data['birth']
    sex = request.data['sex']
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

        p_detail = PInfo(p_fk=p_user)
        p_detail.name = name
        p_detail.birth = birth
        p_detail.sex = sex
        p_detail.save()

        return Response(status=HTTP_201_CREATED)
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


@api_view(['POST', 'PUT'])
@permission_classes((PatientAuthenticated,))
def set_fixed(request):
    token = request.META.get('HTTP_TOKEN')
    p_id = get_id(token)

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

    if request.method == 'POST':
        p_fixed = PFixed(p_id=p_id)
        p_fixed.save()

        res = Response(status=HTTP_201_CREATED)

    else:
        p_fixed = PFixed.objects.get(p_id=p_id)

        res = Response(status=HTTP_200_OK)

    p_fixed.weight = weight
    p_fixed.height = height
    p_fixed.adl = adl
    p_fixed.smoking = smoking
    p_fixed.save()

    p_fixed_condition = PFixedCondition(p_fixed=p_fixed, **condition_data)
    p_fixed_condition.save()

    p_fixed_unique = PFixedUnique(p_fixed=p_fixed, **unique_data)
    p_fixed_unique.save()

    return res


