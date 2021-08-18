from django.db.models import Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from django.core.validators import validate_email
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_406_NOT_ACCEPTABLE

from checkup_backend.settings import ALGORITHM, SECRET_KEY
from patient.models import PLogin, PInfo
import jwt, datetime


def make_token(id):
    payload = {}
    payload['auth'] = 'patient'
    payload['id'] = id
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=300)

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)


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


