# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models


class DLoc(models.Model):
    d_loc_id = models.BigIntegerField(primary_key=True)
    d = models.ForeignKey('DLogin', models.DO_NOTHING)
    nation = models.CharField(max_length=100, blank=True, null=True)
    hospital = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_loc'


class PLogin(models.Model):
    p_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(db_index=True, unique=True, verbose_name='Email Address')
    password = models.CharField(max_length=100, blank=True, null=True)
    agreed = models.IntegerField(blank=True, null=True)
    push_token = models.CharField(max_length=255, blank=True, null=True)
    refresh_token = models.CharField(max_length=255,blank=True, null=True)
    locale = models.CharField(max_length=3, blank=True, null=True)
    code_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_login'


class PPass(models.Model):
    p_pass_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    code = models.IntegerField(blank=True, null=True)
    p_pass_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_pass'


class DPass(models.Model):
    d_pass_id = models.BigAutoField(primary_key=True)
    d = models.ForeignKey('DLogin', models.DO_NOTHING)
    code = models.IntegerField(blank=True, null=True)
    d_pass_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_pass'


class PInfo(models.Model):
    p_info_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    name = models.CharField(max_length=100, blank=True, null=True)
    birth = models.DateField(blank=True, null=True)
    sex = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_info'


class DLogin(models.Model):
    d_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(db_index=True, unique=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    nation = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    hospital = models.CharField(max_length=100, blank=True, null=True)
    push_token = models.CharField(max_length=255, blank=True, null=True)
    refresh_token = models.CharField(max_length=255, blank=True, null=True)
    alert = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_login'


class DLoginAttempt(models.Model):
    d_login_attempt = models.BigAutoField(primary_key=True)
    d = models.ForeignKey(DLogin, models.DO_NOTHING)
    attempt_time = models.DateTimeField(blank=True, null=True)
    attempt_status = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_login_attempt'


class DPRelation(models.Model):
    relation_id = models.BigAutoField(primary_key=True)
    d = models.ForeignKey(DLogin, models.DO_NOTHING)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    add_time = models.DateTimeField(blank=True, null=True)
    discharged = models.IntegerField(blank=True, null=True)
    discharged_time = models.DateTimeField(blank=True, null=True)
    worsened = models.IntegerField(blank=True, null=True)
    cause = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_p_relation'


class DOxygen(models.Model):
    d_oxygen_id = models.BigAutoField(primary_key=True)
    relation = models.ForeignKey(DPRelation, models.DO_NOTHING)
    oxygen_start = models.DateField(blank=True, null=True)
    oxygen_end = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_oxygen'


class DUpdate(models.Model):
    d_update_id = models.BigAutoField(primary_key=True)
    relation = models.ForeignKey(DPRelation, models.DO_NOTHING)
    type = models.IntegerField(blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    seen = models.IntegerField(blank=True, null=True)
    recorded_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'd_update'


class PDCode(models.Model):
    p_d_code_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    code = models.CharField(max_length=4, blank=True, null=True)
    code_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_d_code'


class PDaily(models.Model):
    p_daily_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    p_daily_time = models.DateTimeField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_daily'


class PDailyPredict(models.Model):
    p_daily_predict_id = models.BigAutoField(primary_key=True)
    p_daily = models.ForeignKey(PDaily, models.DO_NOTHING)
    prediction_result = models.FloatField(blank=True, null=True)
    prediction_explaination = models.TextField(blank=True, null=True)
    oxygen = models.FloatField(blank=True, null=True)
    icu = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_daily_predict'


class PDailySymptom(models.Model):
    p_daily_symptom_id = models.BigAutoField(primary_key=True)
    p_daily = models.ForeignKey(PDaily, models.DO_NOTHING)
    hemoptysis = models.IntegerField(blank=True, null=True)
    dyspnea = models.IntegerField(blank=True, null=True)
    chest_pain = models.IntegerField(blank=True, null=True)
    cough = models.IntegerField(blank=True, null=True)
    sputum = models.IntegerField(blank=True, null=True)
    rhinorrhea = models.IntegerField(blank=True, null=True)
    sore_throat = models.IntegerField(blank=True, null=True)
    anosmia = models.IntegerField(blank=True, null=True)
    myalgia = models.IntegerField(blank=True, null=True)
    arthralgia = models.IntegerField(blank=True, null=True)
    fatigue = models.IntegerField(blank=True, null=True)
    headache = models.IntegerField(blank=True, null=True)
    diarrhea = models.IntegerField(blank=True, null=True)
    nausea_vomiting = models.IntegerField(blank=True, null=True)
    chill = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_daily_symptom'


class PDailyTemperature(models.Model):
    p_daily_temperature_id = models.BigAutoField(primary_key=True)
    p_daily = models.ForeignKey(PDaily, models.DO_NOTHING)
    antipyretics = models.IntegerField(blank=True, null=True)
    temp_capable = models.IntegerField(blank=True, null=True)
    temp = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_daily_temperature'


class PFixed(models.Model):
    p_fixed_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey('PLogin', models.DO_NOTHING)
    smoking = models.IntegerField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    adl = models.IntegerField(blank=True, null=True)
    p_fixed_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_fixed'


class PFixedCondition(models.Model):
    p_fixed_condition_id = models.BigAutoField(primary_key=True)
    p_fixed = models.ForeignKey(PFixed, models.DO_NOTHING)
    chronic_cardiac_disease = models.IntegerField(blank=True, null=True)
    chronic_neurologic_disorder = models.IntegerField(blank=True, null=True)
    copd = models.IntegerField(blank=True, null=True)
    asthma = models.IntegerField(blank=True, null=True)
    chronic_liver_disease = models.IntegerField(blank=True, null=True)
    hiv = models.IntegerField(blank=True, null=True)
    autoimmune_disease = models.IntegerField(blank=True, null=True)
    dm = models.IntegerField(blank=True, null=True)
    hypertension = models.IntegerField(blank=True, null=True)
    ckd = models.IntegerField(blank=True, null=True)
    cancer = models.IntegerField(blank=True, null=True)
    heart_failure = models.IntegerField(blank=True, null=True)
    dementia = models.IntegerField(blank=True, null=True)
    chronic_hematologic_disorder = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_fixed_condition'


class PFixedUnique(models.Model):
    p_fixed_unique_id = models.BigAutoField(primary_key=True)
    p_fixed = models.ForeignKey(PFixed, models.DO_NOTHING)
    transplantation = models.IntegerField(blank=True, null=True)
    immunosuppress_agent = models.IntegerField(blank=True, null=True)
    chemotherapy = models.IntegerField(blank=True, null=True)
    pregnancy = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_fixed_unique'


class PLoginAttempt(models.Model):
    p_login_attempt_id = models.BigAutoField(primary_key=True)
    p = models.ForeignKey(PLogin, models.DO_NOTHING)
    attempt_time = models.DateTimeField(blank=True, null=True)
    attempt_status = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'p_login_attempt'
