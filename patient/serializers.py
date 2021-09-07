from rest_framework import serializers

from patient.models import *
from tools import make_token

class FixedCondition(serializers.ModelSerializer):
    class Meta:
        model = PFixedCondition
        fields = '__all__'


class FixedUnique(serializers.ModelSerializer):
    class Meta:
        model = PFixedUnique
        fields = '__all__'


class FixedGet(serializers.ModelSerializer):

    class Meta:
        model = PFixed
        fields = '__all__'

    def to_representation(self, instance):
        field_list = [field.name for field in PFixed._meta.get_fields()]
        field_list.remove('pfixedcondition')
        field_list.remove('pfixedunique')

        data = super().to_representation(instance)

        for field in field_list:
            if data[field] == None:
                data[field] = ''

        data['p_id'] = data['p']
        data.pop('p_fixed_date')
        data.pop('p')
        if instance.p_fixed_id:
            f_condition_id = PFixedCondition.objects.get(p_fixed=instance.p_fixed_id)
            f_unique_id = PFixedUnique.objects.get(p_fixed=instance.p_fixed_id)
            f_condition = FixedCondition(f_condition_id).data
            f_unique = FixedUnique(f_unique_id).data

            f_condition.pop('p_fixed_condition_id')
            f_condition.pop('p_fixed')

            f_unique.pop('p_fixed_unique_id')
            f_unique.pop('p_fixed')

            p_info = dict(list(PInfo.objects.filter(p=data['p_id']).values('name', 'birth', 'sex'))[0])

            data.update(f_condition)
            data.update(f_unique)
            data.update(p_info)


        return data


class PatientLogin(serializers.ModelSerializer):
    class Meta:
        model = PLogin
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.pk:
            return {'token': make_token(instance.pk)}
        return data
