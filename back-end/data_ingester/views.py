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
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from django.http import JsonResponse
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.decorators import api_view, parser_classes
import io


from data_ingester.utils.postgres import (
    get_admissions_with_filters,
    ingest_data
)

time_multiplier = {'ME':12,'W':52,'YE':1,'D':365}
min_data = {'ME':12,'W':102,'YE':6,'D':24}
min_avg = 0.106
max_avg = 30.527

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
children_hospitals = [
    "Primary Childrens Hospital",
    "Primary Childrens Hospital Lehi - Miller Campus"
]

hospital_options = [{'label': "All Hospitals", 'value': 'All'},{'label': "Childrens hospital", 'value': '1'},{'label': "Not childrens hospital", 'value': '0'}]

time_options = []
for time_format in ['day','week','month','year']:
    time_options.append({'label':time_format,'value':time_format})

def get_hospitals_ajax(request):
    hospital_type = request.GET.get('hospital_type')

    if hospital_type == '1':  # Children’s hospitals only
        filtered = [h for h in hospital_locations if h in children_hospitals]
    elif hospital_type == '0':  # Not children’s hospitals
        filtered = [h for h in hospital_locations if h not in children_hospitals]
    else:  # All
        filtered = list(hospital_locations.keys())

    return JsonResponse({'hospitals': filtered})

def prepare_plot_data(df):
    # Separate actual and forecast
    df = df.copy()
    df.rename(columns={'period': 'timestamp'},inplace=True)
    actual_df = df[df['forecast'] == False][['timestamp', 'organization', 'admissions']].copy()
    actual_df['Type'] = 'Actual'
    actual_df.rename(columns={'admissions': 'value'}, inplace=True)

    forecast_df = df[df['forecast'] == True][[
        'timestamp', 'organization',
        'chronos_pred', 'conformal_naive_pred',
        'arima_pred', 'transformer_pred', 'xgb_pred'
    ]].copy()

    # Melt the forecast part
    forecast_long = forecast_df.melt(
        id_vars=['timestamp', 'organization'],
        value_vars=[
            'chronos_pred', 'conformal_naive_pred',
            'arima_pred', 'transformer_pred', 'xgb_pred'
        ],
        var_name='Type',
        value_name='value'
    )

    # Combine actual and forecasted
    combined_df = pd.concat([actual_df, forecast_long], ignore_index=True)
    return combined_df


def plot_covid_admissions_chart(organization=None, child_hospital=None, time_freq=None):
    covid_df = get_admissions_with_filters(disease="covid",time_freq=time_freq,organization=organization,childrens_hospital=child_hospital)
    covid_df_plot = prepare_plot_data(covid_df)
    
    
    line_styles = {
    "Actual": "solid",
    "chronos_pred": "dot",
    "conformal_naive_pred": "dash",
    "arima_pred": "dashdot",
    "transformer_pred": "longdash",
    "xgb_pred": "longdashdot"
    }

    color_map = {
        "Actual": "#1f77b4",  # Blue
        "chronos_pred": "#ff7f0e",  # Orange
        "conformal_naive_pred": "#2ca02c",  # Green
        "arima_pred": "#d62728",  # Red
        "transformer_pred": "#9467bd",  # Purple
        "xgb_pred": "#8c564b",  # Brown
    }
    fig = px.line(
    covid_df_plot,
    x='timestamp',
    y='value',
    color='Type',
    line_dash='Type',
    line_dash_map=line_styles,
    color_discrete_map=color_map,
    markers=True,
    hover_data=['organization', 'value','timestamp']
    )

    fig.update_layout(
        title="COVID-19 Admissions & Forecasts",
        xaxis_title="Date",
        yaxis_title="Admissions / Predictions",
        legend_title="Prediction Type",
        template="plotly_white",
    )

    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(type='date')

    return fig.to_html(full_html=False)
    
    # fig = px.line(
    #         covid_df_plot,
    #         x='timestamp',
    #         y='value',
    #         color='organization',
    #         line_dash='Type',
    #         markers=True
    #     )
    # fig.update_xaxes(type='date') 
    # return fig.to_html(full_html=False)

def plot_covid_admissions_map_chart(organization=None, child_hospital=None, time_freq=None):

    covid_df = get_admissions_with_filters(disease="covid",time_freq=time_freq,organization=organization,childrens_hospital=child_hospital,map=True)
    covid_df_plot = prepare_plot_data(covid_df)
    forecast_dfs = []
    for hospital in covid_df_plot['organization'].unique():
        df_hosp = covid_df_plot[covid_df_plot['organization'] == hospital]
        df_actual = df_hosp[df_hosp['Type'] == 'Actual'].sort_values('timestamp')
        if df_actual.empty:
            continue
        #latest_actual = df_actual['value'].iloc[-1]
        avg_actual = df_actual['value'].mean()
        size = (avg_actual - min_avg) / (max_avg - min_avg + 1e-5) * 40 + 10
        selected_model = "chronos_pred"
        df_pred = df_hosp[df_hosp['Type'] == selected_model].sort_values('timestamp')
        if len(df_pred) < 4:
            continue  
        size_points = df_pred['value'].iloc[:4].values
        X = np.arange(1, 5).reshape(-1, 1)
        y = size_points
        model = LinearRegression()
        model.fit(X, y)
        slope = model.coef_[0] if isinstance(model.coef_, np.ndarray) else model.coef_
        slope = np.clip(slope, -3, 3)
        data = {
            "LATITUDE": [hospital_locations[hospital][0]],
            "LONGITUDE": [hospital_locations[hospital][1]],
            "SIZE": [size],
            "COLOR": [slope],
            "ORGANIZATION": [hospital],
            "FIRST_PRED": int(size_points[0]),
            "SECOND_PRED": int(size_points[1]),
            "THIRD_PRED": int(size_points[2]),
            "FOURTH_PRED": int(size_points[3])
        }
        forecast_dfs.append(pd.DataFrame(data))
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
    lat=final_df["LATITUDE"],
    lon=final_df["LONGITUDE"],
    mode="markers",
    marker=dict(
        size=final_df["SIZE"],  # Scale the size of the markers
        color=final_df["COLOR"],  # Use PRED_LEVEL for coloring
        colorscale="RdBu",  # Choose a colorscale for the PRED_LEVEL values
        colorbar=dict(title="Slope"),  # Add a colorbar to indicate the scale
        showscale=True,
        reversescale = True,
        opacity=0.8,
        line=dict(width=0.5, color="black"),
        cmin=-3,
        cmax=3,
    ),
    text=final_df["ORGANIZATION"] + 
    "<br>" + "Avg Admissions: " + final_df["SIZE"].round(1).astype(str) +
    "<br>" + "First Prediction: " + final_df["FIRST_PRED"].astype(str) +
    "<br>" + "Second Prediction: " + final_df["SECOND_PRED"].astype(str) +
    "<br>" + "Third Prediction: " + final_df["THIRD_PRED"].astype(str) +
    "<br>" + "Fourth Prediction: " + final_df["FOURTH_PRED"].astype(str),
    ))
    fig.update_layout(
        title="Covid Map Admissions & Forecasts",
        margin=dict(l=0, r=0, t=50, b=0),
        height = 600,
        # geo = dict(
        #     scope="usa",
        #     showland=True,
        #     landcolor="gainsboro",
        #     showlakes = False,
        #     center=dict(lat=39.321, lon=-111.093),  # Center the map on Utah
        #     projection_scale=4
        # )
        geo=dict(
            scope="usa",
            showland=True,
            landcolor="lightgray",         # or any from the table above
            showlakes=False,
            showcountries=True,
            countrycolor="gray",            # or "gray" for stronger contrast
            showsubunits=True,
            subunitcolor="gray",           # thin borders within states if needed
            projection=dict(type="albers usa"),
            center=dict(lat=39.321, lon=-111.093),
            projection_scale=4
        )
    )
    return fig.to_html(full_html=False)


def plot_influenza_admissions_chart(organization=None,time_freq=None):
    influenza_df = get_admissions_with_filters(disease="influenza",time_freq=time_freq,organization=organization,childrens_hospital=None)
    influenza_df_plot = prepare_plot_data(influenza_df)
    
    line_styles = {
    "Actual": "solid",
    "chronos_pred": "dot",
    "conformal_naive_pred": "dash",
    "arima_pred": "dashdot",
    "transformer_pred": "longdash",
    "xgb_pred": "longdashdot"
    }
    color_map = {
        "Actual": "#1f77b4",  # Blue
        "chronos_pred": "#ff7f0e",  # Orange
        "conformal_naive_pred": "#2ca02c",  # Green
        "arima_pred": "#d62728",  # Red
        "transformer_pred": "#9467bd",  # Purple
        "xgb_pred": "#8c564b",  # Brown
    }
    fig = px.line(
    influenza_df_plot,
    x='timestamp',
    y='value',
    color='Type',
    line_dash='Type',
    line_dash_map=line_styles,
    color_discrete_map=color_map,
    markers=True
    )
    fig.update_layout(
        title="Influenza Admissions & Forecasts",
        xaxis_title="Date",
        yaxis_title="Admissions / Predictions",
        legend_title="Prediction Type",
        template="plotly_white",
    )
    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(type='date')

    return fig.to_html(full_html=False)
    


def plot_rsv_admissions_chart(organization=None, time_freq=None):
    rsv_df = get_admissions_with_filters(disease="rsv",time_freq=time_freq,organization=organization,childrens_hospital=None)
    rsv_df_plot = prepare_plot_data(rsv_df)
    line_styles = {
    "Actual": "solid",
    "chronos_pred": "dot",
    "conformal_naive_pred": "dash",
    "arima_pred": "dashdot",
    "transformer_pred": "longdash",
    "xgb_pred": "longdashdot"
    }
    color_map = {
        "Actual": "#1f77b4",  # Blue
        "chronos_pred": "#ff7f0e",  # Orange
        "conformal_naive_pred": "#2ca02c",  # Green
        "arima_pred": "#d62728",  # Red
        "transformer_pred": "#9467bd",  # Purple
        "xgb_pred": "#8c564b",  # Brown
    }
    fig = px.line(
    rsv_df_plot,
    x='timestamp',
    y='value',
    color='Type',
    line_dash='Type',
    line_dash_map=line_styles,
    color_discrete_map=color_map,
    markers=True
    )
    fig.update_layout(
        title="RSV Admissions & Forecasts",
        xaxis_title="Date",
        yaxis_title="Admissions / Predictions",
        legend_title="Prediction Type",
        template="plotly_white",
    )
    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(type='date')

    return fig.to_html(full_html=False)

    
    
##Functions for all the views

def covid_admissions_view(request):
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    if timefreq is None or len(timefreq)==0:
        timefreq = "month"
    if hospital == '1':
        filtered_organisations = [hosp for hosp in hospital_locations if hosp in children_hospitals]
    elif hospital == '0':
        filtered_organisations = [hosp for hosp in hospital_locations if hosp not in children_hospitals]
    else:
        filtered_organisations = hospital_locations.keys()
        
    chart_html_covid = plot_covid_admissions_chart(organization, hospital,timefreq)
    
    return render(request, 'covid_admissions.html', {'chart_html_covid': chart_html_covid,
                                                     'organisations': filtered_organisations, 
                                                     'hospital_options':hospital_options,
                                                     'time_options':time_options,
                                                     'hospital': hospital,
                                                     'organization': organization,
                                                     'timefreq': timefreq})

def covid_map_view(request):
    organization = request.GET.get("organization")
    hospital = request.GET.get("hospital")
    timefreq = request.GET.get("timefreq")
    if timefreq is None or len(timefreq)==0:
        timefreq = "month"
    if hospital == '1':
        filtered_organisations = [hosp for hosp in hospital_locations if hosp in children_hospitals]
    elif hospital == '0':
        filtered_organisations = [hosp for hosp in hospital_locations if hosp not in children_hospitals]
    else:
        filtered_organisations = hospital_locations.keys()
    chart_html_covid_map = plot_covid_admissions_map_chart(organization, hospital,timefreq)
    return render(request, 'covid_map_admissions.html', {'chart_html_covid_map': chart_html_covid_map,
                                                         'organisations': filtered_organisations, 
                                                     'hospital_options':hospital_options,
                                                     'time_options':time_options,
                                                     'hospital': hospital,
                                                     'organization': organization,
                                                     'timefreq': timefreq})
    
    
def influenza_admissions_view(request):
    organization = request.GET.get("organization")
    timefreq = request.GET.get("timefreq")
    if organization is None or len(organization)==0:
        organization = "Primary Childrens Hospital"
    
    if timefreq is None or len(timefreq)==0:
        timefreq = "month"
    chart_html_influenza = plot_influenza_admissions_chart(organization,timefreq)
    
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
        timefreq = "month"
    chart_html_rsv = plot_rsv_admissions_chart(organization,timefreq)
    return render(request, 'rsv_admissions.html', {'chart_html_rsv': chart_html_rsv,
                                                   'organisations': hospital_locations.keys(),
                                                     'time_options':time_options,
                                                     'organization': organization,
                                                    'timefreq': timefreq})
    
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_data(request):
    disease_type = request.data.get('disease_type')
    csv_file = request.FILES.get('file')
    
    if not disease_type or not csv_file:
        return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        file_data = csv_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(file_data))
        
        #Validation Steps
        required_columns = ["EMPI","ADMIT_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            return Response(
                {'error': f'Missing required columns: {", ".join(missing)}', 'progress': 0},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            df['ADMIT_DTS'] = pd.to_datetime(df['ADMIT_DTS'])
        except ValueError:
            return Response(
                {'error': 'Date format of ADMIT_DTS column is wrong', 'progress': 0,},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        ingest_data(df,disease_type)
        return Response({'message': 'File uploaded successfully', 'progress': 100,}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e), 'progress': 0,}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
