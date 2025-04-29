from django.shortcuts import render
from django.http import HttpResponse
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
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
# Create your views here.

from influxdb_ingester.utils.influx import (
    create_influx_client,
    query_data
)

time_multiplier = {'ME':12,'W':52,'YE':1,'D':365}
min_data = {'ME':12,'W':102,'YE':6,'D':24}

hospital_locations = {
    "Primary Childrens Hospital":(40.771111, -111.838889),
    "Cassia Regional Hospital":(42.5351, -113.7819),
    "McKay-Dee Hospital":(41.1834, -111.9539),
    "McKay-Dee Behavioral Health":(41.1839, -111.9550),
    "Primary Childrens Behavioral Health":(40.77686151556483, -111.84155643373789),
    "Utah Valley Hospital":(40.2478, -111.6658),
    "American Fork Hospital":(40.3804, -111.7672),
    "Intermountain Medical Center":(40.6595, -111.8918),
    "St George Regional Hospital":(37.0968, -113.5540),
    "Cedar City Hospital":(37.6997, -113.0663),
    "Logan Regional Hospital":(41.7556, -111.8215),
    "Garfield Memorial Hospital":(37.8264, -112.4269),
    "Riverton Hospital":(40.5205, -111.9805),
    "LDS Hospital":(40.7785, -111.8803),
    "Park City Hospital":(40.6877, -111.4694),
    "Sanpete Valley Hospital":(39.5315,-111.4610),
    "Alta View Hospital":(40.5771, -111.8540),
    "Bear River Valley Hospital":(41.7243, -112.1823),
    "Layton Hospital":(41.0518, -111.9687),
    "Delta Community Hospital":(39.3501, -112.5610),
    "Spanish Fork Hospital":(40.1150, -111.6549),
    "Sevier Valley Hospital":(38.7826, -112.0838),
    "Fillmore Community Hospital":(38.9547, -112.3403),
    "Primary Childrens Hospital Lehi - Miller Campus":(40.4148764717385, -111.8992368087777),
    "Heber Valley Hospital":(40.4902, -111.4062),
    "Primary Childrens Lehi Behavioral Health - Miller Campus":(40.5148764717385, -111.9992368087777)
}

hospital_options = [{'label': "All Hospitals", 'value': 'All'},{'label': "Childrens hospital", 'value': '1'},{'label': "Not childrens hospital", 'value': '0'}]

time_options = []
for time_format in ['WEEKLY','YEARLY','DAILY']:
    if time_format=="YEARLY":
        time_options.append({'label':time_format,'value':time_format[:2]})
    else:
        time_options.append({'label':time_format,'value':time_format[0]})
        
time_options.insert(0, {'label': 'MONTHLY', 'value': 'ME'})



INFLUXDB_TOKEN="u9-rX6MNrziGfs2Fq6d4f9JNl_XWN6_DmxmciDtDUY9w8ehkgZxm9Axp4iuqUIhygsiEGC1tkPFtxt9h6G8hHg=="
INFLUXDB_ORG="Shiva"
INFLUXDB_URL="http://localhost:8086"
INFLUXDB_BUCKET="timeseriesprediction"

def get_data(measurement:str):
    # Flux query to select data from the "covid" measurement and pivot the fields
    influx_token = INFLUXDB_TOKEN
    influx_url = INFLUXDB_URL
    influx_org = INFLUXDB_ORG
    bucket_name = INFLUXDB_BUCKET
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


def plot_covid_admissions_chart(covid_df,organization=None, child_hospital=None, time_freq=None):
    if organization:
        covid_df = covid_df[covid_df['ORGANIZATION_NM'] == organization]
    if child_hospital and child_hospital!='All':
        covid_df = covid_df[covid_df['CHILDRENS_HOSPITAL'] == child_hospital]
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

def plot_covid_admissions_map_chart(covid_df,organization=None, hospital=None, time_freq=None):
    if organization:
        covid_df = covid_df[covid_df['ORGANIZATION_NM'] == organization]
    if hospital:
        covid_df = covid_df[covid_df['CHILDRENS_HOSPITAL'] == hospital]
    forecast_dfs = []
    for hospital in covid_df['ORGANIZATION_NM'].unique():
        df_hosp = covid_df[covid_df['ORGANIZATION_NM'] == hospital]

        df_hosp = df_hosp.groupby([pd.Grouper(key='timestamp',freq=time_freq), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        
        if len(df_hosp) <= min_data[time_freq]: 
            size_points = df_hosp["ADMISSIONS"].iloc[-4:].values
            X = np.array(range(1,len(size_points)+1)).reshape(-1,1)
            y = size_points
            model = LinearRegression()
            model.fit(X,y)
            slope = model.coef_[0][0] if isinstance(model.coef_[0], np.ndarray) else model.coef_[0]
            data = {
            "LATITUDE":[hospital_locations[hospital][0]],
            "LONGITUDE":[hospital_locations[hospital][1]],
            "SIZE": [df_hosp["ADMISSIONS"].iloc[-1]],
            "PRED_LEVEL" : [0],
            "COLOR":[slope],
            "ORGANIZATION":[hospital]
            }
            forecast_dfs.append(pd.DataFrame(data))
            continue
        
        df_hosp_series = TimeSeries.from_dataframe(df_hosp,time_col='timestamp',value_cols="ADMISSIONS",fill_missing_dates=True, freq=time_freq).pd_dataframe()
        series_filled = TimeSeries.from_dataframe(df_hosp_series.fillna(method="ffill"))
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast = model.predict(4).pd_dataframe()
        circle = series_filled.values()[-1][0]
        size_points = forecast.iloc[:4].values
        X = np.array(range(1, 5)).reshape(-1, 1)
        y = size_points
        model = LinearRegression()
        model.fit(X,y)
        slope = model.coef_[0][0] if isinstance(model.coef_[0], np.ndarray) else model.coef_[0]
        prev = circle
        for i in range(5):
            if circle==prev:
                data = {
                    "LATITUDE":[hospital_locations[hospital][0]],
                    "LONGITUDE":[hospital_locations[hospital][1]],
                    "SIZE":[circle],
                    "PRED_LEVEL" : [i], 
                    "COLOR":[slope],
                    "ORGANIZATION":[hospital]
                    }
                forecast_dfs.append(pd.DataFrame(data))
            if i>=4:
                break
            circle += max(0,forecast.iloc[i,0]-prev)
            prev = forecast.iloc[i,0]
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
    lat=final_df["LATITUDE"],
    lon=final_df["LONGITUDE"],
    mode="markers",
    marker=dict(
        size=final_df["SIZE"]*5,  # Scale the size of the markers
        color=final_df["COLOR"],  # Use PRED_LEVEL for coloring
        colorscale="RdBu",  # Choose a colorscale for the PRED_LEVEL values
        colorbar=dict(title="COLOR"),  # Add a colorbar to indicate the scale
        showscale=True,  # Show the color scale
        reversescale = True,
        cmin=final_df["COLOR"].quantile(0.05),  # Set the lower bound (5th percentile)
        cmax=final_df["COLOR"].quantile(0.95),
    ),
    text=final_df["ORGANIZATION"] + "<br>" + "Admissions: " + final_df["SIZE"].astype(str)+ "<br>" + "Prediction "+time_freq+": "+final_df["PRED_LEVEL"].astype(str),
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height = 500,
        geo = dict(
            scope="usa",
            showland=True,
            landcolor="rgb(117, 117, 117)",
            showlakes=True,
            lakecolor="rgb(117,117,117)",
            center=dict(lat=39.321, lon=-111.093),  # Center the map on Utah
            projection_scale=4
        )
    )
    return fig.to_html(full_html=False)


def plot_influenza_admissions_chart(influenza_df,organization=None, time_freq=None):
    if organization:
        influenza_df = influenza_df[influenza_df['ORGANIZATION_NM'] == organization]
        
    if len(influenza_df)==0:
        fig = px.line(title="Influenza Time Series prediction")
        fig.update_xaxes(
        dtick="M1",  # Show each month
        tickformat="%b",  # Display month names (Jan, Feb, etc.)
        title="Month"
        )
        fig.update_yaxes(
        title="No. of Admissions"
        )
        return fig.to_html(full_html=False)
        
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



def plot_rsv_admissions_chart(rsv_df,organization=None, time_freq=None):
    if organization:
        rsv_df = rsv_df[rsv_df['ORGANIZATION_NM'] == organization]
        
    if len(rsv_df)==0:
        fig = px.line(title="RSV Time Series prediction")
        fig.update_xaxes(
        dtick="M1",  # Show each month
        tickformat="%b",  # Display month names (Jan, Feb, etc.)
        title="Month"
        )
        fig.update_yaxes(
        title="No. of Admissions"
        )
        return fig.to_html(full_html=False)
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
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    
    if timefreq is None or len(timefreq)==0:
        timefreq = "ME"
    df = get_data("covid")
    chart_html_covid = plot_covid_admissions_chart(df, organization, hospital,timefreq)
    
    return render(request, 'covid_admissions.html', {'chart_html_covid': chart_html_covid,
                                                     'organisations': hospital_locations.keys(), 
                                                     'hospital_options':hospital_options,
                                                     'time_options':time_options,
                                                     'hospital': hospital,
                                                     'timefreq': timefreq})

def covid_map_view(request):
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    
    if timefreq is None or len(timefreq)==0:
        timefreq = "ME"
    df = get_data("covid")
    chart_html_covid_map = plot_covid_admissions_map_chart(df, organization, hospital,timefreq)
    return render(request, 'covid_map_admissions.html', {'chart_html_covid_map': chart_html_covid_map,
                                                         'organisations': hospital_locations.keys(), 
                                                     'hospital_options':hospital_options,
                                                     'time_options':time_options})
    
    
def influenza_admissions_view(request):
    organization = request.GET.get("organization")
    timefreq = request.GET.get("timefreq")
    if organization is None or len(organization)==0:
        organization = "Primary Childrens Hospital"
    
    if timefreq is None or len(timefreq)==0:
        timefreq = "ME"
    df = get_data("influenza")
    chart_html_influenza = plot_influenza_admissions_chart(df, organization,timefreq)
    
    return render(request, 'influenza_admissions.html', {'chart_html_influenza': chart_html_influenza,
                                                         'organisations': hospital_locations.keys(),
                                                     'time_options':time_options,
                                                     'organization': organization,
                                                    'timefreq': timefreq})

def rsv_admissions_view(request):
    organization = request.GET.get("organization")
    timefreq = request.GET.get("timefreq")
    
    if organization is None or len(organization)==0:
        organization = "Primary Childrens Hospital"
    
    if timefreq is None or len(timefreq)==0:
        timefreq = "ME"
    df = get_data("rsv")
    chart_html_rsv = plot_rsv_admissions_chart(df, organization,timefreq)
    return render(request, 'rsv_admissions.html', {'chart_html_rsv': chart_html_rsv,
                                                   'organisations': hospital_locations.keys(),
                                                     'time_options':time_options,
                                                     'organization': organization,
                                                    'timefreq': timefreq})
    
    
@api_view(['POST'])
def ingest_one_record(request):
    data = request.data
    
    try:
        send_to_kafka('test', data)
        return Response({'message': 'Data sent to Kafka'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    
    
    
            