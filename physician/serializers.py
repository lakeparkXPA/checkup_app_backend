from rest_framework import serializers
from patient.models import *

from tools import make_token


class DLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = DLogin
        fields = '__all__'


class PhysicianLogin(serializers.ModelSerializer):
    class Meta:
        model = DLogin
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.pk:
            return {'token': make_token(instance.pk, auth='physician')}
        return data
