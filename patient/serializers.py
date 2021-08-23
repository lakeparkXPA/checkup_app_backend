from rest_framework import serializers

from patient.models import PLogin


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = PLogin
        fields = '__all__'

