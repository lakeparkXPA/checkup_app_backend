from django.db.models import Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from django.core.validators import validate_email
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_201_CREATED

from checkup_backend.settings import ALGORITHM, SECRET_KEY
from patient.models import PLogin, PInfo
import jwt, datetime

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
    try:
        try:
            validate_email(email)
        except:
            raise ValueError('email_format')
        else:
            try:
                db_pass = PLogin.objects.get(email=email).password

                if db_pass != password:
                    raise ValueError('wrong_password')
                else:
                    payload = {}
                    payload['auth'] = 'patient'
                    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=300)

                    token = jwt.encode(payload, SECRET_KEY, ALGORITHM)

                    return Response({'token': token}, status=HTTP_200_OK)

            except PLogin.DoesNotExist:
                raise ValueError('wrong_email')
    except Exception as e:
        return Response({"message": str(e)}, status=HTTP_400_BAD_REQUEST)


