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
        return authenticate(self.context['request'], **kwargs)

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

        # If required, is the email verified?
        # if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
        # from allauth.account import app_settings
        # if app_settings.EMAIL_VERIFICATION ==
        #	app_settings.EmailVerificationMethod.MANDATORY:
        # email_address = user.emailaddress_set.get(email=user.email)
        # if not email_address.verified:
        # raise serializers.ValidationError(_('E-mail is not verified.'))
        attrs['user'] = user
        return attrs


class CustomRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if email and email_address_exists(email):
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."))
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', '')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user