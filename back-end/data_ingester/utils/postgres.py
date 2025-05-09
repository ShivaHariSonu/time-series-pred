import pandas as pd
from models import CovidRecord
from django.db import transaction
from typing import Optional, Union
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.db import connection

def read_csv_data(file_path: str) -> pd.DataFrame:
    """
    Read CSV data from the provided file path.
    """
    df = pd.read_csv(file_path, parse_dates=['ADMIT_DTS'])
    return df

def delete_forecasted_covid_records() -> int:
    """
    Delete all previous forecasted Covid rows.
    Returns the number of records deleted.
    """
    with transaction.atomic():
        deleted_count, _ = CovidRecord.objects.filter(forecast=True).delete()
    return deleted_count

def get_admissions_since(start_timestamp: Optional[Union[str, datetime]] = None):
    if start_timestamp:
        if isinstance(start_timestamp, str):
            start_timestamp = pd.to_datetime(start_timestamp)
        sql = """
            SELECT *
            FROM covid_data
            WHERE timestamp >= %s
            ORDER BY admit_dts
        """
        params = [start_timestamp]
    else:
        sql = """
            SELECT 
                *
            FROM covid_data
            ORDER BY timestamp
        """
        params = []
        
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=cols)
    

def ingest_covid_data(new_covid_df: pd.DataFrame):
    """
    Ingest CSV data points into InfluxDB.
    Logic
    1) Delete forecasted values in Postgres
    2)Take all the values from the postgres
    3) Convert all the new values from CSV file to postgres format
    4) Run predictions
    5) Insert all the records to postgres
    """
    
    #Fetching older data
    delete_forecasted_covid_records()
    old_covid_data = get_admissions_since()
    
    
    new_covid_df = new_covid_df[["EMPI","ADMIT_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
    new_covid_df = new_covid_df.rename(columns={'ADMIT_DTS': 'timestamp'})
    new_covid_df['timestamp'] = pd.to_datetime(new_covid_df['timestamp'].dt.tz_localize(None))
    new_covid_df["ADMISSIONS"] = new_covid_df.groupby(["timestamp", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')
    
    
    
    
            
            
    
    


    # df = df.rename(columns={'_time': 'timestamp'})
    # df_filtered = df[["EMPI","timestamp","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
    # df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'].dt.tz_localize(None))
    # df_filtered["ADMISSIONS"] = df_filtered.groupby(["timestamp", "ORGANIZATION_NM", "CHILDRENS_HOSPITAL"])["EMPI"].transform('count')

    # forecast_dfs = []
    # for hospital in covid_df['ORGANIZATION_NM'].unique():
    #     df_hosp = covid_df[covid_df['ORGANIZATION_NM'] == hospital]
    #     df_hosp = df_hosp.groupby([pd.Grouper(key='timestamp',freq=time_freq), 'ORGANIZATION_NM', 'CHILDRENS_HOSPITAL']).agg({'ADMISSIONS': 'sum'}).reset_index()
    #     if len(df_hosp) <= min_data[time_freq]: 
    #         df_hosp['Type'] = 'Actual'
    #         forecast_dfs.append(df_hosp)
    #         continue
    #     series = TimeSeries.from_dataframe(df_hosp,time_col='timestamp',value_cols="ADMISSIONS",fill_missing_dates=True, freq=time_freq)
    #     df = series.pd_dataframe()
    #     df_filled = df.ffill()
    #     series_filled = TimeSeries.from_dataframe(df_filled)
    #     model = ExponentialSmoothing(seasonal_periods=None)
    #     model.fit(series_filled)
    #     forecast_horizon = 4
    #     forecast = model.predict(forecast_horizon)
    #     forecast_df = forecast.pd_dataframe()
    #     forecast_df['timestamp'] = forecast_df.index
    #     forecast_df['ORGANIZATION_NM'] = hospital
    #     forecast_df['Type'] = 'Forecast'  # Mark as forecasted data
    #     df_hosp['Type'] = 'Actual'
    #     forecast_dfs.append(df_hosp)
    #     forecast_dfs.append(forecast_df)
    # final_df = pd.concat(forecast_dfs, ignore_index=True)