from django.db import models

# Create your models here.

class CovidRecord(models.Model):
    timestamp = models.DateTimeField()
    organization = models.CharField(max_length=255)
    childrens_hospital = models.BooleanField()
    admissions = models.IntegerField()
    forecast = models.BooleanField()
    exponential_smoothing_pred = models.IntegerField()
    chronos_pred = models.IntegerField()
    class Meta:
        db_table = 'covid_data'