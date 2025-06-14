# Generated by Django 5.1.7 on 2025-05-18 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingester', '0002_alter_covidrecord_admissions_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfluenzaRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('organization', models.CharField(max_length=255)),
                ('childrens_hospital', models.BooleanField()),
                ('admissions', models.FloatField(blank=True, null=True)),
                ('forecast', models.BooleanField()),
                ('chronos_pred', models.FloatField(blank=True, null=True)),
                ('conformal_naive_pred', models.FloatField(blank=True, null=True)),
                ('arima_pred', models.FloatField(blank=True, null=True)),
                ('transformer_pred', models.FloatField(blank=True, null=True)),
                ('xgb_pred', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RSVRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('organization', models.CharField(max_length=255)),
                ('childrens_hospital', models.BooleanField()),
                ('admissions', models.FloatField(blank=True, null=True)),
                ('forecast', models.BooleanField()),
                ('chronos_pred', models.FloatField(blank=True, null=True)),
                ('conformal_naive_pred', models.FloatField(blank=True, null=True)),
                ('arima_pred', models.FloatField(blank=True, null=True)),
                ('transformer_pred', models.FloatField(blank=True, null=True)),
                ('xgb_pred', models.FloatField(blank=True, null=True)),
            ],
        ),
    ]
