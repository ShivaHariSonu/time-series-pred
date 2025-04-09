from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import pandas as pd
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode
import plotly.express as px
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .kafka import send_to_kafka
# Create your views here.

from influxdb_ingester.utils.influx import (
    create_influx_client,
    query_data
)

time_multiplier = {'ME':12,'W':52,'YE':1,'D':365}
min_data = {'ME':12,'W':102,'YE':6,'D':24}


def get_data(measurement:str):
    # Flux query to select data from the "covid" measurement and pivot the fields
    conf = settings.INFLUXDB_SETTINGS
    influx_token = conf['token']
    influx_url = conf['url']
    influx_org = conf['org']
    bucket_name = conf['bucket']
    query = f'''
    from(bucket: "{bucket_name}")
      |> range(start: 0)
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    client = create_influx_client(influx_url,influx_token,influx_org)
    df = query_data(client,influx_org,query)
    df = df.rename(columns={'_time': 'timestamp'})
    df_filtered = df[["EMPI","timestamp","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
    df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'].dt.tz_localize(None))
    df_filtered["ADMISSIONS"] = df_filtered.groupby(["timestamp", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')
    return df_filtered


def plot_covid_admissions_chart(covid_df,organization=None, hospital=None, time_freq=None):
    if organization:
        covid_df = covid_df[covid_df['ORGANIZATION_NM'] == organization]
    if hospital:
        covid_df = covid_df[covid_df['CHILDRENS_HOSPITAL'] == hospital]
    forecast_dfs = []
    for hospital in covid_df['ORGANIZATION_NM'].unique():
        df_hosp = covid_df[covid_df['ORGANIZATION_NM'] == hospital]
        df_hosp = df_hosp.groupby([pd.Grouper(key='timestamp',freq=time_freq), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        if len(df_hosp) <= min_data[time_freq]: 
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            continue
        series = TimeSeries.from_dataframe(df_hosp,time_col='timestamp',value_cols="ADMISSIONS",fill_missing_dates=True, freq=time_freq)
        df = series.pd_dataframe()
        df_filled = df.fillna(method="ffill")
        series_filled = TimeSeries.from_dataframe(df_filled)
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast_horizon = (2028 - df_hosp['timestamp'].dt.year.max()) * time_multiplier[time_freq]
        forecast = model.predict(forecast_horizon)
        forecast_df = forecast.pd_dataframe()
        forecast_df['timestamp'] = forecast_df.index
        forecast_df['ORGANIZATION_NM'] = hospital
        forecast_df['Type'] = 'Forecast'  # Mark as forecasted data
        df_hosp['Type'] = 'Actual'
        forecast_dfs.append(df_hosp)
        forecast_dfs.append(forecast_df)
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    fig = px.line(
            final_df,
            x='timestamp',
            y='ADMISSIONS',
            color='ORGANIZATION_NM',
            line_dash='Type',
            markers=True,
            title="Admissions with Forecast up to 2028"
        )
    fig.update_xaxes(type='date') 
    return fig.to_html(full_html=False)


def plot_influenza_admissions_chart(influenza_df,organization=None, hospital=None, time_freq=None):
    if organization:
        influenza_df = influenza_df[influenza_df['ORGANIZATION_NM'] == organization]
    if hospital:
        influenza_df = influenza_df[influenza_df['CHILDRENS_HOSPITAL'] == hospital]
    forecast_dfs = []
    for hospital in influenza_df['ORGANIZATION_NM'].unique():
        df_hosp = influenza_df[influenza_df['ORGANIZATION_NM'] == hospital]
        df_hosp = df_hosp.groupby([pd.Grouper(key='timestamp',freq=time_freq), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        if len(df_hosp) <= min_data[time_freq]: 
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            continue
        series = TimeSeries.from_dataframe(df_hosp,time_col='timestamp',value_cols="ADMISSIONS",fill_missing_dates=True, freq=time_freq)
        df = series.pd_dataframe()
        df_filled = df.fillna(method="ffill")
        series_filled = TimeSeries.from_dataframe(df_filled)
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast_horizon = (2028 - df_hosp['timestamp'].dt.year.max()) * time_multiplier[time_freq]
        forecast = model.predict(forecast_horizon)
        forecast_df = forecast.pd_dataframe()
        forecast_df['timestamp'] = forecast_df.index
        forecast_df['ORGANIZATION_NM'] = hospital
        forecast_df['Type'] = 'Forecast'  # Mark as forecasted data
        df_hosp['Type'] = 'Actual'
        forecast_dfs.append(df_hosp)
        forecast_dfs.append(forecast_df)
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    final_df["YEAR"] = final_df["timestamp"].dt.year
    final_df["NORMALIZED_DATE"] = final_df["timestamp"].apply(lambda d: d.replace(year=2020)) 
    fig = px.line(
            final_df,
            x='NORMALIZED_DATE',
            y='ADMISSIONS',
            color="YEAR",
            line_dash='Type',  # Different line styles for actual vs. forecast
            title="Influenza Time Series prediction",
            labels={"ADMISSIONS": "No. of Admissions", "NORMALIZED_DATE": "Month"},
            facet_row="ORGANIZATION_NM"
        )
    fig.update_xaxes(
    dtick="M1",  # Show each month
    tickformat="%b",  # Display month names (Jan, Feb, etc.)
    title="Month"
    )
    return fig.to_html(full_html=False)



def plot_rsv_admissions_chart(rsv_df,organization=None, hospital=None, time_freq=None):
    if organization:
        rsv_df = rsv_df[rsv_df['ORGANIZATION_NM'] == organization]
    if hospital:
        rsv_df = rsv_df[rsv_df['CHILDRENS_HOSPITAL'] == hospital]
    forecast_dfs = []
    for hospital in rsv_df['ORGANIZATION_NM'].unique():
        df_hosp = rsv_df[rsv_df['ORGANIZATION_NM'] == hospital]
        df_hosp = df_hosp.groupby([pd.Grouper(key='timestamp',freq=time_freq), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        if len(df_hosp) <= min_data[time_freq]: 
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            continue
        series = TimeSeries.from_dataframe(df_hosp,time_col='timestamp',value_cols="ADMISSIONS",fill_missing_dates=True, freq=time_freq)
        df = series.pd_dataframe()
        df_filled = df.fillna(method="ffill")
        series_filled = TimeSeries.from_dataframe(df_filled)
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast_horizon = (2028 - df_hosp['timestamp'].dt.year.max()) * time_multiplier[time_freq]
        forecast = model.predict(forecast_horizon)
        forecast_df = forecast.pd_dataframe()
        forecast_df['timestamp'] = forecast_df.index
        forecast_df['ORGANIZATION_NM'] = hospital
        forecast_df['Type'] = 'Forecast'  # Mark as forecasted data
        df_hosp['Type'] = 'Actual'
        forecast_dfs.append(df_hosp)
        forecast_dfs.append(forecast_df)
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    final_df["YEAR"] = final_df["timestamp"].dt.year
    final_df["NORMALIZED_DATE"] = final_df["timestamp"].apply(lambda d: d.replace(year=2020)) 
    fig = px.line(
            final_df,
            x='NORMALIZED_DATE',
            y='ADMISSIONS',
            color="YEAR",
            line_dash='Type',  # Different line styles for actual vs. forecast
            title="RSV Time Series prediction",
            labels={"ADMISSIONS": "No. of Admissions", "NORMALIZED_DATE": "Month"},
            facet_row="ORGANIZATION_NM"
        )
    fig.update_xaxes(
    dtick="M1",  # Show each month
    tickformat="%b",  # Display month names (Jan, Feb, etc.)
    title="Month"
    )
    return fig.to_html(full_html=False)

    
    
##Functions for all the views

def covid_admissions_view(request):
    # Retrieve filter parameters from the GET request (if any)
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    
    if timefreq is None:
        timefreq = "ME"
    # Load and process data
    df = get_data("covid")
    # Generate Plotly chart HTML after applying filters
    chart_html_covid = plot_covid_admissions_chart(df, organization, hospital,timefreq)
    
    # Render the chart in the Django template
    return render(request, 'covid_admissions.html', {'chart_html_covid': chart_html_covid})
    
    
def influenza_admissions_view(request):
    # Retrieve filter parameters from the GET request (if any)
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    
    if timefreq is None:
        timefreq = "ME"
    # Load and process data
    df = get_data("influenza")
    # Generate Plotly chart HTML after applying filters
    chart_html_influenza = plot_influenza_admissions_chart(df, organization, hospital,timefreq)
    
    # Render the chart in the Django template
    return render(request, 'influenza_admissions.html', {'chart_html_influenza': chart_html_influenza})

def rsv_admissions_view(request):
    # Retrieve filter parameters from the GET request (if any)
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    
    if timefreq is None:
        timefreq = "ME"
    # Load and process data
    df = get_data("rsv")
    # Generate Plotly chart HTML after applying filters
    chart_html_rsv = plot_rsv_admissions_chart(df, organization, hospital,timefreq)
    
    # Render the chart in the Django template
    return render(request, 'rsv_admissions.html', {'chart_html_rsv': chart_html_rsv})
    
    
@api_view(['POST'])
def ingest_one_record(request):
    data = request.data
    try:
        send_to_kafka('test', data)
        return Response({'message': 'Data sent to Kafka'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    
    
    
            