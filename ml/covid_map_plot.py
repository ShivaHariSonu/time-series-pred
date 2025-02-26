import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode


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
    "Cassia Regional Hospital":(42.5351, -113.7819),
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

covid_df_filtered["ADMISSIONS"] = covid_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

org_options = [{'label': org, 'value': org} for org in covid_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = [{'label': str(hosp), 'value': hosp} for hosp in covid_df_filtered['CHILDRENS_HOSPITAL'].unique()]
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = [{'label':time_format,'value':time_format[0]} for time_format in ['Week','Yearly','Daily']]
time_options.insert(0, {'label': 'Month', 'value': 'M'})

time_multiplier = {'M':12,'W':12,'Y':1,'D':60}



def severity_to_radius(severity_value, min_radius, max_radius):
    return ((severity_value + 10) / 20) * (max_radius - min_radius) + min_radius


max_radius = 20
min_radius = 5 

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Monthly Admissions Dashboard", style={'textAlign': 'center'}),

    # Dropdown for Organization Name
    html.Label("Select Organization:"),
    dcc.Dropdown(id='org_filter', options=org_options, value='All', clearable=False),

    # Dropdown for Children's Hospital
    html.Label("Children's Hospital Filter:"),
    dcc.Dropdown(id='hospital_filter', options=hospital_options, value='All', clearable=False),
    
    # Dropdown for granularity
    html.Label("Timeframe Filter:"),
    dcc.Dropdown(id='time_filter', options=time_options, value='M', clearable=False),

    # Graph
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

    # Apply filters
    if selected_org != 'All':
        filtered_df = filtered_df[filtered_df['ORGANIZATION_NM'] == selected_org]
    if selected_hospital != 'All':
        filtered_df = filtered_df[filtered_df['CHILDRENS_HOSPITAL'] == selected_hospital]

    forecast_dfs = []
    for hospital in filtered_df['ORGANIZATION_NM'].unique():
        df_hosp = filtered_df[filtered_df['ORGANIZATION_NM'] == hospital]

        df_hosp = df_hosp.groupby([pd.Grouper(key='DATE',freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        
        if len(df_hosp) <= time_multiplier[selected_time]:  # Skip hospitals with insufficient data
            data = {
            "LATITUDE":[hospital_locations[hospital][0]],
            "LONGITUDE":[hospital_locations[hospital][1]],
            "SEVERE": [0],
            "ORGANIZATION":[hospital]
            }
            forecast_dfs.append(pd.DataFrame(data))
            continue
        
        # Convert to Darts TimeSeries
        series = TimeSeries.from_dataframe(df_hosp,time_col='DATE',value_cols="ADMISSIONS",fill_missing_dates=True, freq=selected_time)
        df = series.pd_dataframe()

        # Apply the forward fill on the DataFrame
        df_filled = df.fillna(method="ffill")

        series_filled = TimeSeries.from_dataframe(df_filled)
        # Fit and forecast
        model = ExponentialSmoothing(seasonal_periods=None)
        model.fit(series_filled)
        forecast_horizon = 4
        forecast = model.predict(forecast_horizon)

        forecast_df = forecast.pd_dataframe()
        data = {
            "LATITUDE":[hospital_locations[hospital][0]],
            "LONGITUDE":[hospital_locations[hospital][1]],
            "SEVERE": [forecast_df.iloc[3,0]-forecast_df.iloc[0,0]],
            "ORGANIZATION":[hospital]
            }
        forecast_dfs.append(pd.DataFrame(data))

    # Combine all forecasts
    final_df = pd.concat(forecast_dfs, ignore_index=True)
    final_df["SIZE"] = abs(final_df["SEVERE"])*50
    
    fig = px.scatter_mapbox(
    final_df,
    lat="LATITUDE",
    lon="LONGITUDE",
    size="SIZE",
    color="SEVERE",
    hover_name="ORGANIZATION",
    color_continuous_scale="Bluered",  # Blue to Red scale
    size_max=max_radius,
    zoom=4,
    mapbox_style="open-street-map"
    )

    fig.update_layout(title="Hospital Severity Map",height=800)
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
