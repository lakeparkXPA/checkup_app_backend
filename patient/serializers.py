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

            try:
                p_info = dict(list(PInfo.objects.filter(p=data['p_id']).values('name', 'birth', 'sex'))[0])
                p_info['email'] = PLogin.objects.get(p_id=data['p_id']).email
            except:
                p_info = {"name": "", "birth": "", "sex": "", "email": ""}

            data.update(f_condition)
            data.update(f_unique)
            data.update(p_info)


        return data


class DailySymptom(serializers.ModelSerializer):
    class Meta:
        model = PDailySymptom
        fields = '__all__'


class DailyPredict(serializers.ModelSerializer):
    class Meta:
        model = PDailyPredict
        fields = '__all__'


class DailyTemperature(serializers.ModelSerializer):
    class Meta:
        model = PDailyTemperature
        fields = '__all__'


class DailyGet(serializers.ModelSerializer):

    class Meta:
        model = PDaily
        fields = '__all__'

    def to_representation(self, instance):
        field_list = [field.name for field in PDaily._meta.get_fields()]
        field_list.remove('pdailysymptom')
        field_list.remove('pdailypredict')
        field_list.remove('pdailytemperature')


        data = super().to_representation(instance)

        for field in field_list:
            if data[field] == None:
                data[field] = ''

        data['p_id'] = data['p']
        data.pop('p')
        if instance.p_daily_id:
            d_symptom_id = PDailySymptom.objects.get(p_daily=instance.p_daily_id)
            d_temp_id = PDailyTemperature.objects.get(p_daily=instance.p_daily_id)
            d_predict_id = PDailyPredict.objects.get(p_daily=instance.p_daily_id)

            d_symptom = DailySymptom(d_symptom_id).data
            d_temp = DailyTemperature(d_temp_id).data
            d_predict = DailyPredict(d_predict_id).data

            d_symptom.pop('p_daily_symptom_id')
            d_symptom.pop('p_daily')

            d_temp.pop('p_daily_temperature_id')
            d_temp.pop('p_daily')

            d_predict.pop('p_daily_predict_id')
            d_predict.pop('p_daily')

            data.update(d_symptom)
            data.update(d_temp)
            data.update(d_predict)


        return data



class PatientLogin(serializers.ModelSerializer):
    class Meta:
        model = PLogin
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.pk:
            return {'token': make_token(instance.pk), 'refresh_token': make_token(instance.pk, auth='refresh', hours=5)}
        return data
