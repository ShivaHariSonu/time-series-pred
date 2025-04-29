import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode


file_path = "../../datasets/germ_watch_data/germwatch_influenza_hospitalizations_20241029_135917.csv"
influenza_df = pd.read_csv(file_path)


influenza_df_filtered = influenza_df[["EMPI","COLLECTED_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
influenza_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
influenza_df_filtered['DATE'] = pd.to_datetime(influenza_df_filtered['DATE'])
influenza_df_filtered["ADMISSIONS"] = influenza_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

org_options = [{'label': org, 'value': org} for org in influenza_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = []
hospital_options.append({'label': "Childrens hospital", 'value': 1})
hospital_options.append({'label': "Not childrens hospital", 'value': 0})
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = []
for time_format in ['WEEKLY','YEARLY','DAILY']:
    if time_format=="YEARLY":
        time_options.append({'label':time_format,'value':time_format[:2]})
    else:
        time_options.append({'label':time_format,'value':time_format[0]})
        
time_options.insert(0, {'label': 'Month', 'value': 'ME'})


time_multiplier = {'ME':12,'W':52,'YE':1,'D':365}

min_data = {'ME':12,'W':102,'YE':6,'D':24}

def create_influenza_layout():
    layout = html.Div([
        html.H1("Influenza Time Series Prediction", style={'textAlign': 'center'}),
        
        html.Label("Select Organization:"),
        dcc.Dropdown(id='influenza_org_filter', options=org_options, value='Primary Childrens Hospital', clearable=False),

        html.Label("Children's Hospital Filter:"),
        dcc.Dropdown(id='influenza_hospital_filter', options=hospital_options, value=1, clearable=False),

        html.Label("Timeframe Filter:"),
        dcc.Dropdown(id='influenza_time_filter', options=time_options, value='ME', clearable=False),

        dcc.Graph(id='influenza_admissions_graph', config={'displayModeBar': False})
    ])
    return layout

def register_influenza_callbacks(app):
    @app.callback(
        Output('influenza_admissions_graph', 'figure'),
        [Input('influenza_time_filter','value'),
            Input('influenza_org_filter', 'value'),
        Input('influenza_hospital_filter', 'value')]
    )
    def update_graph(selected_time, selected_org, selected_hospital):
        filtered_df = influenza_df_filtered.copy()


        # Apply filters
        if selected_org != 'All':
            filtered_df = filtered_df[filtered_df['ORGANIZATION_NM'] == selected_org]
        if selected_hospital != 'All':
            filtered_df = filtered_df[filtered_df['CHILDRENS_HOSPITAL'] == selected_hospital]

        forecast_dfs = []
        for hospital in filtered_df['ORGANIZATION_NM'].unique():
            df_hosp = filtered_df[filtered_df['ORGANIZATION_NM'] == hospital]

            df_hosp = df_hosp.groupby([pd.Grouper(key='DATE',freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
            

            if len(df_hosp) <= min_data[selected_time]:  # Skip hospitals with insufficient data
                df_hosp['Type'] = 'Actual'
                forecast_dfs.append(df_hosp)
                continue
            
            # Convert to Darts TimeSeries
            series = TimeSeries.from_dataframe(df_hosp,time_col='DATE',value_cols="ADMISSIONS",fill_missing_dates=True, freq=selected_time)
            df = series.pd_dataframe()

            # Apply the forward fill on the DataFrame
            df_filled = df.fillna(method="ffill")

            # Convert the DataFrame back to a TimeSeries
            series_filled = TimeSeries.from_dataframe(df_filled)
            # Fit and forecast
            model = ExponentialSmoothing(seasonal_periods=None)
            model.fit(series_filled)
            forecast_horizon = (2028 - df_hosp['DATE'].dt.year.max()) * time_multiplier[selected_time]
            forecast = model.predict(forecast_horizon)

            # Convert forecast to DataFrame
            forecast_df = forecast.pd_dataframe()
            forecast_df['DATE'] = forecast_df.index
            forecast_df['ORGANIZATION_NM'] = hospital
            forecast_df['Type'] = 'Forecast'  # Mark as forecasted data

            # Append both actual and forecasted data
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            forecast_dfs.append(forecast_df)

        # Combine all forecasts
        final_df = pd.concat(forecast_dfs, ignore_index=True)
        final_df["YEAR"] = final_df["DATE"].dt.year
        final_df["NORMALIZED_DATE"] = final_df["DATE"].apply(lambda d: d.replace(year=2020)) 
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
        return fig
