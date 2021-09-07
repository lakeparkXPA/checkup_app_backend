import jwt

from rest_framework import permissions
from rest_framework import exceptions

from checkup_backend.settings import ALGORITHM, SECRET_KEY


class PatientAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.META.get('HTTP_TOKEN')
        if token is None:
            return False
        else:
            try:
                decoded_token = jwt.decode(token, SECRET_KEY, ALGORITHM)
            except:
                raise exceptions.AuthenticationFailed('token_expire')

            if decoded_token['auth'] == 'patient':
                return True
            else:
                return False


class PhysicianAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.META.get('HTTP_TOKEN')
        if token is None:
            return False
        else:
            try:
                decoded_token = jwt.decode(token, SECRET_KEY, ALGORITHM)
            except:
                raise exceptions.AuthenticationFailed('token_expire')

            if decoded_token['auth'] == 'physician':
                return True
            else:
                return False

