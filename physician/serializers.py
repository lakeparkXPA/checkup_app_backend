from rest_framework import serializers
from physician.models import *


class DLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = DLogin
        fields = '__all__'