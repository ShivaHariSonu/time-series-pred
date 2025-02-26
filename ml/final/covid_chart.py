import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode


file_path = "../../datasets/germ_watch_data/germwatch_covid_hospitalizations_20241029_140153.csv"
covid_df = pd.read_csv(file_path)


covid_df_filtered = covid_df[["EMPI","COLLECTED_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
covid_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
covid_df_filtered['DATE'] = pd.to_datetime(covid_df_filtered['DATE'])
covid_df_filtered["ADMISSIONS"] = covid_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')


org_options = [{'label': org, 'value': org} for org in covid_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})
hospital_options = []
hospital_options.append({'label': "Childrens hospital", 'value': 1})
hospital_options.append({'label': "Not childrens hospital", 'value': 0})
hospital_options.insert(0, {'label': 'All', 'value': 'All'})
time_options = [{'label':time_format,'value':time_format[0]} for time_format in ['Week','Yearly','Daily']]
time_options = []
for time_format in ['WEEKLY','YEARLY','DAILY']:
    if time_format=="YEARLY":
        time_options.append({'label':time_format,'value':time_format[:2]})
    else:
        time_options.append({'label':time_format,'value':time_format[0]})
        
time_options.insert(0, {'label': 'Month', 'value': 'ME'})





time_multiplier = {'ME':12,'W':52,'YE':1,'D':365}

min_data = {'ME':12,'W':102,'YE':6,'D':24}

def create_covid_layout():
    layout = html.Div([
        html.H1("Covid Admissions Dashboard", style={'textAlign': 'center'}),
        html.Label("Select Organization:"),
        dcc.Dropdown(id='covid_org_filter', options=org_options, value='All', clearable=False),
        html.Label("Children's Hospital Filter:"),
        dcc.Dropdown(id='covid_hospital_filter', options=hospital_options, value='All', clearable=False),
        html.Label("Timeframe Filter:"),
        dcc.Dropdown(id='covid_time_filter', options=time_options, value='ME', clearable=False),
        dcc.Graph(id='covid_admissions_graph', config={'displayModeBar': False})
    ])
    return layout

def register_covid_callbacks(app):
    @app.callback(
        Output('covid_admissions_graph', 'figure'),
        [Input('covid_time_filter','value'),
            Input('covid_org_filter', 'value'),
        Input('covid_hospital_filter', 'value')]
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
                df_hosp['Type'] = 'Actual'
                forecast_dfs.append(df_hosp)
                continue
            series = TimeSeries.from_dataframe(df_hosp,time_col='DATE',value_cols="ADMISSIONS",fill_missing_dates=True, freq=selected_time)
            df = series.pd_dataframe()
            df_filled = df.fillna(method="ffill")
            series_filled = TimeSeries.from_dataframe(df_filled)
            model = ExponentialSmoothing(seasonal_periods=None)
            model.fit(series_filled)
            forecast_horizon = (2028 - df_hosp['DATE'].dt.year.max()) * time_multiplier[selected_time]
            forecast = model.predict(forecast_horizon)
            forecast_df = forecast.pd_dataframe()
            forecast_df['DATE'] = forecast_df.index
            forecast_df['ORGANIZATION_NM'] = hospital
            forecast_df['Type'] = 'Forecast'  # Mark as forecasted data
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            forecast_dfs.append(forecast_df)

        # Combine all forecasts
        final_df = pd.concat(forecast_dfs, ignore_index=True)
        fig = px.line(
            final_df,
            x='DATE',
            y='ADMISSIONS',
            color='ORGANIZATION_NM',
            line_dash='Type',
            markers=True,
            title="Monthly Admissions with Forecast up to 2028"
        )
        fig.update_xaxes(type='date')  
        return fig
