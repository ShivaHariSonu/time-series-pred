from django.db import models

# Create your models here.

class CovidRecord(models.Model):
    timestamp = models.DateTimeField()
    organization = models.CharField(max_length=255)
    childrens_hospital = models.BooleanField()
    admissions = models.FloatField(null=True, blank=True)
    forecast = models.BooleanField()
    chronos_pred = models.FloatField(null=True, blank=True)
    conformal_naive_pred = models.FloatField(null=True, blank=True)
    arima_pred = models.FloatField(null=True, blank=True)
    transformer_pred = models.FloatField(null=True, blank=True)
    xgb_pred = models.FloatField(null=True, blank=True)
    

class InfluenzaRecord(models.Model):
    timestamp = models.DateTimeField()
    organization = models.CharField(max_length=255)
    childrens_hospital = models.BooleanField()
    admissions = models.FloatField(null=True, blank=True)
    forecast = models.BooleanField()
    chronos_pred = models.FloatField(null=True, blank=True)
    conformal_naive_pred = models.FloatField(null=True, blank=True)
    arima_pred = models.FloatField(null=True, blank=True)
    transformer_pred = models.FloatField(null=True, blank=True)
    xgb_pred = models.FloatField(null=True, blank=True)
    
class RSVRecord(models.Model):
    timestamp = models.DateTimeField()
    organization = models.CharField(max_length=255)
    childrens_hospital = models.BooleanField()
    admissions = models.FloatField(null=True, blank=True)
    forecast = models.BooleanField()
    chronos_pred = models.FloatField(null=True, blank=True)
    conformal_naive_pred = models.FloatField(null=True, blank=True)
    arima_pred = models.FloatField(null=True, blank=True)
    transformer_pred = models.FloatField(null=True, blank=True)
    xgb_pred = models.FloatField(null=True, blank=True)