import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from darts.utils.utils import ModelMode, SeasonalityMode


file_path = "../datasets/germ_watch_data/germwatch_rsv_hospitalizations_20241029_135427.csv"
rsv_df = pd.read_csv(file_path)


rsv_df_filtered = rsv_df[["EMPI","COLLECTED_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
rsv_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
rsv_df_filtered['DATE'] = pd.to_datetime(rsv_df_filtered['DATE'])
rsv_df_filtered["ADMISSIONS"] = rsv_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

org_options = [{'label': org, 'value': org} for org in rsv_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = [{'label': str(hosp), 'value': hosp} for hosp in rsv_df_filtered['CHILDRENS_HOSPITAL'].unique()]
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = [{'label':time_format,'value':time_format[0]} for time_format in ['Week','Daily']]
time_options.insert(0, {'label': 'Month', 'value': 'M'})

time_multiplier = {'M':12,'W':52,'D':365}

min_data = {'M':12,'W':102,'D':24}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("RSV Time Series Prediction", style={'textAlign': 'center'}),

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
    filtered_df = rsv_df_filtered.copy()
    # filtered_df = (
    #     rsv_df_filtered_copy
    #     .groupby([pd.Grouper(freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL'])
    #     .agg({'ADMISSIONS': 'sum'})
    #     .reset_index()
    # )

    # Apply filters
    if selected_org != 'All':
        filtered_df = filtered_df[filtered_df['ORGANIZATION_NM'] == selected_org]
    if selected_hospital != 'All':
        filtered_df = filtered_df[filtered_df['CHILDRENS_HOSPITAL'] == selected_hospital]

    forecast_dfs = []
    for hospital in filtered_df['ORGANIZATION_NM'].unique():
        df_hosp = filtered_df[filtered_df['ORGANIZATION_NM'] == hospital]

        df_hosp = df_hosp.groupby([pd.Grouper(key='DATE',freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
        
        # df_hosp = df_hosp.resample(selected_time).sum().fillna(0)
        
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
        title="RSV Time Series Prediction",
        labels={"ADMISSIONS": "No. of Admissions", "NORMALIZED_DATE": "Month"},
        facet_row="ORGANIZATION_NM"
    )
    fig.update_xaxes(
    dtick="M1",  # Show each month
    tickformat="%b",  # Display month names (Jan, Feb, etc.)
    title="Month"
    )
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
