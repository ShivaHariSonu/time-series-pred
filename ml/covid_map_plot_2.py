import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np


file_path = "../datasets/germ_watch_data/germwatch_covid_hospitalizations_20241029_140153.csv"
covid_df = pd.read_csv(file_path)

hospital_locations = {
    "Primary Childrens Hospital":(40.771111, -111.838889),
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

covid_df_filtered = covid_df[["EMPI","COLLECTED_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL" ]]
covid_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
covid_df_filtered['DATE'] = pd.to_datetime(covid_df_filtered['DATE'])
covid_df_filtered = covid_df_filtered[covid_df_filtered["ORGANIZATION_NM"]!="Cassia Regional Hospital"]
covid_df_filtered["ADMISSIONS"] = covid_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

org_options = [{'label': org, 'value': org} for org in covid_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = [{'label': str(hosp), 'value': hosp} for hosp in covid_df_filtered['CHILDRENS_HOSPITAL'].unique()]
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = [{'label':time_format,'value':time_format[0]} for time_format in ['Week','Yearly','Daily']]
time_options.insert(0, {'label': 'Month', 'value': 'M'})

min_data = {'M':12,'W':102,'Y':6,'D':24}


colors = ["red", "blue", "green", "orange", "purple"]


max_radius = 70
min_radius = 10

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Monthly Admissions Dashboard", style={'textAlign': 'center'}),

    html.Label("Select Organization:"),
    dcc.Dropdown(id='org_filter', options=org_options, value='All', clearable=False),

    html.Label("Children's Hospital Filter:"),
    dcc.Dropdown(id='hospital_filter', options=hospital_options, value='All', clearable=False),
    
    html.Label("Timeframe Filter:"),
    dcc.Dropdown(id='time_filter', options=time_options, value='M', clearable=False),

    dcc.Graph(id='admissions_graph')
])


@app.callback(
    Output('admissions_graph', 'figure'),
    [Input('time_filter','value'),
        Input('org_filter', 'value'),
     Input('hospital_filter', 'value')]
)
def update_graph(selected_time, selected_org, selected_hospital):
    
    filtered_df = covid_df_filtered.copy()
    if selected_org != 'All':
        filtered_df = filtered_df[filtered_df['ORGANIZATION_NM'] == selected_org]
    if selected_hospital != 'All':
        filtered_df = filtered_df[filtered_df['CHILDRENS_HOSPITAL'] == selected_hospital]

    forecast_dfs = []
    for hospital in filtered_df['ORGANIZATION_NM'].unique():
        df_hosp = filtered_df[filtered_df['ORGANIZATION_NM'] == hospital]

        df_hosp = df_hosp.groupby([pd.Grouper(key='DATE',freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        
        if len(df_hosp) <= min_data[selected_time]: 
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
        
        series = TimeSeries.from_dataframe(df_hosp,time_col='DATE',value_cols="ADMISSIONS",fill_missing_dates=True, freq=selected_time)
        df = series.pd_dataframe()

        df_filled = df.fillna(method="ffill")

        series_filled = TimeSeries.from_dataframe(df_filled)
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast_horizon = 4
        forecast = model.predict(forecast_horizon)

        forecast_df = forecast.pd_dataframe()
        circle = series_filled.values()[-1][0]
        size_points = forecast_df.iloc[:4].values
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
            circle += max(0,forecast_df.iloc[i,0]-prev)
            prev = forecast_df.iloc[i,0]

    # Combine all forecasts
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    
    
    fig = go.Figure()
    
    # fig.add_trace(go.Scattergeo(
    #     lat=final_df["LATITUDE"],
    #     lon=final_df["LONGITUDE"],
    #     name = final_df["PRED_LEVEL"],
    #     mode="markers",
    #     marker=dict(
    #         size = final_df["SIZE"]*5,
    #         color=final_df["COLOR"]),
    #     text=final_df["ORGANIZATION"]
    # ))
    fig.add_trace(go.Scattergeo(
    lat=final_df["LATITUDE"],
    lon=final_df["LONGITUDE"],
    mode="markers",
    marker=dict(
        size=final_df["SIZE"] * 5,  # Scale the size of the markers
        color=final_df["COLOR"]*5,  # Use PRED_LEVEL for coloring
        colorscale="RdBu",  # Choose a colorscale for the PRED_LEVEL values
        colorbar=dict(title="COLOR"),  # Add a colorbar to indicate the scale
        showscale=True,  # Show the color scale
        reversescale = True
    ),
    text=final_df["ORGANIZATION"] + "<br>" + "Admissions: " + final_df["SIZE"].astype(str)+ "<br>" + "Prediction "+selected_time+": "+final_df["PRED_LEVEL"].astype(str),
    ))

    

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height = 800,
        geo = dict(
            scope="usa",
            showland=True,
            landcolor="rgb(217, 217, 217)",
            center=dict(lat=39.321, lon=-111.093),  # Center the map on Utah
            projection_scale=4
        )
    )


    
    
    # fig = px.scatter_mapbox(
    # final_df,
    # lat="LATITUDE",
    # lon="LONGITUDE",
    # size="SIZE",
    # color="PRED_LEVEL",
    # hover_name="ORGANIZATION",
    # size_max=max_radius,
    # zoom=6,
    # center = {"lat": 39.321, "lon": -111.093},
    # mapbox_style="open-street-map",
    # color_discrete_sequence=["red", "blue", "green", "orange", "purple"] 
    # )
    # fig.update_layout(title="Hospital Severity Map", height=800)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
