from rest_framework import serializers
from patient.models import *

from tools import make_token
import datetime


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


class PInfoData(serializers.ModelSerializer):
    class Meta:
        model = PInfo
        fields = ('name', 'birth', 'sex')


class DPfixed(serializers.ModelSerializer):
    class Meta:
        model = DPRelation
        fields = 'discharged'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.p:
            p_info_id = PInfo.objects.get(p=instance.p)

            p_info = PInfoData(p_info_id).data


            data.update(p_info)
            born = datetime.datetime.strptime(data['birth'], "%Y-%m-%d")
            today = datetime.datetime.today()

            data['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

        return data
