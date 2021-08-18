from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists



from patient.models import PLogin


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = PLogin
        fields = '__all__'


class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        auth = authenticate(self.context['request'], **kwargs)
        print(auth)
        return auth

    def _validate_email(self, email, password):
        user = None
        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise ValidationError(msg)
        return user

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = self._validate_email(email, password)

        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise ValidationError(msg)

        # If requireds, is the email verified?
        # if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
        # from allauth.account import app_settings
        # if app_settings.EMAIL_VERIFICATION ==
        #	app_settings.EmailVerificationMethod.MANDATORY:
        # email_address = user.emailaddress_set.get(email=user.email)
        # if not email_address.verified:
        # raise serializers.ValidationError(_('E-mail is not verified.'))
        attrs['user'] = user
        return attrs



class PatientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    agreed = serializers.BooleanField(write_only=True)

    name = serializers.CharField(write_only=True)
    birth = serializers.DateField(write_only=True)
    sex = serializers.CharField(write_only=True)

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        print(self.cleaned_data)

        adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])

        user.password = self.cleaned_data['password1']
        user.agreed = self.cleaned_data['agreed']

        user.save()

        from patient.models import PInfo
        p_info = PInfo()
        p_info.p = user
        p_info.name = self.cleaned_data['name']
        p_info.birth = self.cleaned_data['birth']
        p_info.sex = self.cleaned_data['sex']
        p_info.save()

        return user