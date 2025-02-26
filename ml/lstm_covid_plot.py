import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from darts import TimeSeries
from darts.utils.utils import ModelMode, SeasonalityMode
from darts.models import RNNModel
import numpy as np
from darts.metrics import mape

# Load and preprocess data
file_path = "../datasets/germ_watch_data/germwatch_covid_hospitalizations_20241029_140153.csv"
covid_df = pd.read_csv(file_path)
covid_df_filtered = covid_df[["EMPI", "COLLECTED_DTS", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
covid_df_filtered.rename(columns={"COLLECTED_DTS": "DATE"}, inplace=True)
covid_df_filtered['DATE'] = pd.to_datetime(covid_df_filtered['DATE'])
covid_df_filtered["ADMISSIONS"] = covid_df_filtered.groupby(["DATE", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

# Precompute hospital metadata (children's hospital status)
hospital_metadata = covid_df_filtered.groupby('ORGANIZATION_NM')['CHILDRENS_HOSPITAL'].first().to_dict()

# Caches for aggregated data and models
aggregated_data_cache = {}
model_cache = {}

# Dashboard setup
org_options = [{'label': org, 'value': org} for org in covid_df_filtered['ORGANIZATION_NM'].unique()]
org_options.insert(0, {'label': 'All', 'value': 'All'})

hospital_options = [{'label': str(hosp), 'value': hosp} for hosp in covid_df_filtered['CHILDRENS_HOSPITAL'].unique()]
hospital_options.insert(0, {'label': 'All', 'value': 'All'})

time_options = [{'label': time_format, 'value': time_format[0]} for time_format in ['Week', 'Yearly', 'Daily']]
time_options.insert(0, {'label': 'Month', 'value': 'M'})

time_multiplier = {'M': 24, 'W': 24, 'Y': 2, 'D': 32}

def evaluate_lstm(series, model):

    backtest_preds = model.historical_forecasts(series, 
                                                start=0.7,  # Train on first 70% and predict progressively
                                                forecast_horizon=1, 
                                                stride=1,  # Move forward 1 step at a time
                                                retrain=False,  # Retrain model at each step
                                                verbose=True)

    # Compute Mean Absolute Percentage Error (MAPE)
    error = mape(series, backtest_preds)
    return error

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
    [Input('time_filter', 'value'),
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
        # Generate cache keys
        data_cache_key = (hospital, selected_time, selected_hospital)
        model_cache_key = (hospital, selected_time, selected_hospital)

        # Try to retrieve cached data
        if data_cache_key in aggregated_data_cache:
            df_hosp, series_filled = aggregated_data_cache[data_cache_key]
        else:
            # Filter hospital data and apply children's hospital filter
            hosp_data = covid_df_filtered[covid_df_filtered['ORGANIZATION_NM'] == hospital]

            # Aggregate data
            df_hosp = hosp_data.groupby([pd.Grouper(key='DATE', freq=selected_time), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()

            # Handle short series
            if len(df_hosp) <= time_multiplier.get(selected_time, 12):
                aggregated_data_cache[data_cache_key] = (df_hosp, None)
                continue

            # Convert to TimeSeries and preprocess
            series = TimeSeries.from_dataframe(df_hosp, 'DATE', 'ADMISSIONS', fill_missing_dates=True, freq=selected_time)
            df_filled = series.pd_dataframe().ffill()
            series_filled = TimeSeries.from_dataframe(df_filled).astype(np.float32)
            aggregated_data_cache[data_cache_key] = (df_hosp, series_filled)

        # Retrieve from cache
        df_hosp, series_filled = aggregated_data_cache[data_cache_key]

        if series_filled is None:
            df_hosp['Type'] = 'Actual'
            forecast_dfs.append(df_hosp)
            continue

        # Model training with cache
        if model_cache_key in model_cache:
            model = model_cache[model_cache_key]
        else:
            model = RNNModel(model='LSTM', input_chunk_length=time_multiplier[selected_time], n_epochs=50, hidden_dim =256, n_rnn_layers=6, dropout= 0.1, random_state=42,  optimizer_kwargs={'lr': 1e-3})
            model.fit(series_filled)
            print(f"Backtesting MAPE: {evaluate_lstm(series=series_filled,model=model):.2f}% for hospital {hospital}")

            model_cache[model_cache_key] = model

        # Generate forecast
        forecast_horizon = (2028 - df_hosp['DATE'].dt.year.max()) * time_multiplier.get(selected_time, 12)
        forecast = model.predict(forecast_horizon)

        # Prepare forecast dataframe
        forecast_df = forecast.pd_dataframe().reset_index()
        forecast_df.columns = ['DATE', 'ADMISSIONS']
        forecast_df['ORGANIZATION_NM'] = hospital
        forecast_df['Type'] = 'Forecast'

        df_hosp['Type'] = 'Actual'
        forecast_dfs.extend([df_hosp, forecast_df])

    # Create visualization
    final_df = pd.concat(forecast_dfs, ignore_index=True) if forecast_dfs else pd.DataFrame()
    fig = px.line(
        final_df,
        x='DATE',
        y='ADMISSIONS',
        color='ORGANIZATION_NM',
        line_dash='Type',
        markers=True,
        title=f"Admissions Forecast up to 2028 ({selected_time})"
    ) if not final_df.empty else px.line(title="No Data Available")
    fig.update_xaxes(type='date')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)