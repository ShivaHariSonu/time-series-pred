from django.urls import path
from . import views

urlpatterns = [
    path('covid-admissions/', views.covid_admissions_view, name='covid_admissions'),
    path('covid-map-view/', views.covid_map_view, name='covid_map_view'),
    path('influenza-admissions/', views.influenza_admissions_view, name='influenza_admissions'),
    path('rsv-admissions/', views.rsv_admissions_view, name='rsv_admissions'),
    path('get-hospitals/', views.get_hospitals_ajax, name='get_hospitals_ajax'),
    path('upload-data/',views.upload_data,name='upload-data')
]