import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
from ..models import CovidRecord,InfluenzaRecord,RSVRecord
from django.db import transaction
from typing import Optional, Union
from datetime import datetime
from django.utils.dateparse import parse_datetime
import numpy as np
import torch
from chronos import ChronosPipeline
from darts import TimeSeries
from darts.models import NaiveSeasonal, ARIMA, TFTModel, XGBModel
from sqlalchemy import create_engine
import os

engine_URL = "postgresql://"+os.environ.get("POSTGRES_USERNAME")+":"+os.environ.get("POSTGRES_PASSWORD")+"@"+os.environ.get("POSTGRES_HOST")+":"+os.environ.get("POSTGRES_PORT")+"/"+os.environ.get("POSTGRES_DATABASE_NAME")

engine = create_engine(engine_URL)    
    

def read_csv_data(file_path: str) -> pd.DataFrame:
    """
    Read CSV data from the provided file path.
    """
    df = pd.read_csv(file_path, parse_dates=['ADMIT_DTS'])
    return df

def delete_forecasted_records(disease) -> int:
    """
    Delete all previous forecasted Covid rows.
    Returns the number of records deleted.
    """
    if disease=="covid":
        with transaction.atomic():
            deleted_count, _ = CovidRecord.objects.filter(forecast=True).delete()
        return deleted_count
    elif disease=="influenza":
        with transaction.atomic():
            deleted_count, _ = InfluenzaRecord.objects.filter(forecast=True).delete()
        return deleted_count
    else:
        with transaction.atomic():
            deleted_count, _ = RSVRecord.objects.filter(forecast=True).delete()
        return deleted_count
        
        

def get_admissions_since(table_name,start_timestamp: Optional[Union[str, datetime]] = None):
    if start_timestamp:
        if isinstance(start_timestamp, str):
            start_timestamp = pd.to_datetime(start_timestamp)
        sql = f'''
            SELECT *
            FROM {table_name}
            WHERE timestamp >= {start_timestamp}
            ORDER BY timestamp
        '''
    else:
        sql = f'''
            SELECT *
            FROM {table_name}
            ORDER BY timestamp
        '''
    with engine.connect() as connection:
        return pd.read_sql(sql,connection)

def get_admissions_with_filters(disease,time_freq,organization,childrens_hospital, map=False):
    table_name = f"public.data_ingester_{disease}record"
    query = f"""
        SELECT
            DATE_TRUNC(%s, timestamp) AS period,
            organization,
            forecast,
            SUM(CASE WHEN forecast = FALSE THEN admissions ELSE NULL END) AS admissions,
            SUM(CASE WHEN forecast = TRUE THEN chronos_pred ELSE NULL END) AS chronos_pred,
            SUM(CASE WHEN forecast = TRUE THEN conformal_naive_pred ELSE NULL END) AS conformal_naive_pred,
            SUM(CASE WHEN forecast = TRUE THEN arima_pred ELSE NULL END) AS arima_pred,
            SUM(CASE WHEN forecast = TRUE THEN transformer_pred ELSE NULL END) AS transformer_pred,
            SUM(CASE WHEN forecast = TRUE THEN xgb_pred ELSE NULL END) AS xgb_pred
        FROM {table_name}
        WHERE 
            (organization = %s OR %s IS NULL) AND
            (childrens_hospital = %s OR %s IS NULL)
        GROUP BY period, organization,forecast
        ORDER BY organization, period ASC
    """
    if childrens_hospital=='All':
        childrens_hospital = None
    if organization is not None and len(organization)==0:
        organization = None
    params = (time_freq,organization, organization, childrens_hospital, childrens_hospital)
    with engine.connect() as connection:
        df = pd.read_sql_query(query, connection, params=params)
        if map:
            return df
        df_sorted = df.sort_values(by='forecast')
        df_deduped = df_sorted.drop_duplicates(subset=['period', 'organization'], keep='first')
        df_deduped_sorted = df_deduped.sort_values(by=['organization','period'],ascending=[True,True])
        
        forecast_false_df = df_deduped_sorted[df_deduped_sorted['forecast'] == False]
        forecast_true_df = df_deduped_sorted[df_deduped_sorted['forecast'] == True]
        forecast_true_top4 = forecast_true_df.groupby('organization').head(4)
        final_df = pd.concat([forecast_false_df, forecast_true_top4]).sort_values(by=['organization', 'period']).reset_index(drop=True)
        return final_df

    
def convert_to_darts_series(df_hosp):
    ts = TimeSeries.from_dataframe(df_hosp, time_col="timestamp", value_cols="admissions", fill_missing_dates=True, freq='D').astype(np.float32)
    return ts

def run_all_models(df_hosp, forecast_horizon, naive_model_freq,arima_model_freq, tft_model_freq,xgb_model_freq):
    series = convert_to_darts_series(df_hosp)
    
    predictions = {}

    # 1. Conformal Naive (using NaiveSeasonal as base model)
    naive_model = NaiveSeasonal(K=naive_model_freq)
    if len(series)<=naive_model_freq:
        predictions['conformal_naive'] = [0]*forecast_horizon
    else:   
        naive_model.fit(series)
        naive_model_values = naive_model.predict(forecast_horizon).values()
        predictions['conformal_naive'] = naive_model_values.flatten()

    # 2. ARIMA
    arima_model = ARIMA()
    if len(series)<=arima_model_freq:
        predictions['arima'] = [0]*forecast_horizon
    else:
        arima_model.fit(series)
        arima_model_values = arima_model.predict(forecast_horizon).values()
        predictions['arima'] = arima_model_values.flatten()
    
    # 3. Transformer (TFT)
    tft_model = TFTModel(
        input_chunk_length=tft_model_freq,
        output_chunk_length=forecast_horizon,
        n_epochs=2,
        add_encoders = {
            'position': {'future': ['relative']}
        },
        random_state=42
    )
    if len(series)<=tft_model_freq+forecast_horizon:
        predictions['transformer'] = [0]*forecast_horizon
    else:
        tft_model.fit(series)
        tft_model_values = tft_model.predict(forecast_horizon).values()
        predictions['transformer'] = tft_model_values.flatten()
    # 4. XGB Model
    xgb_model = XGBModel(lags=xgb_model_freq, output_chunk_length=forecast_horizon)
    if len(series)<=forecast_horizon+xgb_model_freq:
        predictions['xgb'] = [0]*forecast_horizon
    else:
        xgb_model.fit(series)
        xgb_model_values = xgb_model.predict(forecast_horizon).values()
        predictions['xgb'] = xgb_model_values.flatten()
    return predictions



def ingest_data(new_df: pd.DataFrame, disease:str):
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
    delete_forecasted_records(disease)
    table_name = "data_ingester_"+disease+"record"
    old_data = get_admissions_since(table_name=table_name)
    
    new_df = new_df[["EMPI","ADMIT_DTS","ORGANIZATION_NM", "CHILDRENS_HOSPITAL"]]
    new_df = new_df.rename(columns={'ADMIT_DTS': 'timestamp', 'ORGANIZATION_NM':'organization','CHILDRENS_HOSPITAL':'childrens_hospital'})
    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'].dt.tz_localize(None))
    new_df['admissions'] = new_df.groupby(["timestamp", "organization", "childrens_hospital"])["EMPI"].transform('count')
    new_df = new_df.groupby([pd.Grouper(key='timestamp',freq='D'), 'organization', 'childrens_hospital']).agg({'admissions': 'sum'}).reset_index()
    combined_df = pd.concat([old_data,new_df],ignore_index=True)
    
    forecast_horizon = 120
    chronos_pipeline = ChronosPipeline.from_pretrained("amazon/chronos-t5-tiny")
    
    forecast_dfs = []
    for hospital in combined_df['organization'].unique():
        df_hosp = combined_df[combined_df['organization']==hospital]
        start_date = df_hosp['timestamp'].min()
        end_date = df_hosp['timestamp'].max()
        full_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        future_dates = pd.date_range(start = end_date+pd.tseries.frequencies.to_offset('D'), periods=forecast_horizon,freq='D')
        full_df = pd.DataFrame({'timestamp': full_dates})
        df_hosp = full_df.merge(df_hosp, on='timestamp', how='left')
        df_hosp['admissions'] =  df_hosp['admissions'].fillna(0)
        df_hosp['admissions'] = df_hosp['admissions'].infer_objects(copy=False).astype(int)
        df_hosp['organization'] = hospital
        df_hosp['childrens_hospital'] = df_hosp['childrens_hospital'].ffill().bfill()
        df_hosp['childrens_hospital'] = df_hosp['childrens_hospital'].infer_objects(copy=False).astype(bool)
        
        context = torch.tensor(df_hosp['admissions'].values.astype(np.float32),dtype=torch.float32)
        
        #Check Unsqueeze and Squeeze
        quantiles, chronos_mean = chronos_pipeline.predict_quantiles(context=context,prediction_length=forecast_horizon, quantile_levels=[0.1, 0.5, 0.9])
        chronos_mean_flattened = chronos_mean.numpy().flatten()
        chronos_mean_flattened[np.isnan(chronos_mean_flattened)] = 0
        
        if disease=="covid":
            darts_preds = run_all_models(df_hosp[['timestamp', 'admissions']], forecast_horizon, naive_model_freq=7,arima_model_freq=3,tft_model_freq=7,xgb_model_freq=7)
        else:
            darts_preds = run_all_models(df_hosp[['timestamp', 'admissions']], forecast_horizon, naive_model_freq=365,arima_model_freq=365,tft_model_freq=365,xgb_model_freq=365)
        
        forecast_df = pd.DataFrame({
            'timestamp': future_dates,
            'chronos_pred': chronos_mean_flattened,
            'conformal_naive_pred':darts_preds['conformal_naive'],
            'arima_pred':darts_preds['arima'],
            'transformer_pred':darts_preds['transformer'],
            'xgb_pred':darts_preds['xgb'],
            'organization': [hospital]*forecast_horizon,
            'childrens_hospital': [df_hosp['childrens_hospital'].iloc[0]]*forecast_horizon,
            'forecast': [True]*forecast_horizon
        })
        
        df_hosp['forecast'] = False
        forecast_dfs.append(df_hosp)
        forecast_dfs.append(forecast_df)
    final_df = pd.concat(forecast_dfs,ignore_index=True)
    
    #Insert records to Postgres
    records = []
    if disease=="covid":
        for _, row in final_df.iterrows():
            records.append(CovidRecord(
                timestamp=row['timestamp'],
                organization=row['organization'],
                childrens_hospital=row['childrens_hospital'],
                admissions=row['admissions'],
                forecast=row['forecast'],
                chronos_pred=row['chronos_pred'],
                conformal_naive_pred=row['conformal_naive_pred'],
                transformer_pred=row['transformer_pred'],
                arima_pred = row['arima_pred'],
                xgb_pred=row['xgb_pred']
            ))
        
        # Batch insert in transaction
        with transaction.atomic():
            CovidRecord.objects.bulk_create(records, batch_size=1000)
    elif disease=="influenza":
        for _, row in final_df.iterrows():
            records.append(InfluenzaRecord(
                timestamp=row['timestamp'],
                organization=row['organization'],
                childrens_hospital=row['childrens_hospital'],
                admissions=row['admissions'],
                forecast=row['forecast'],
                chronos_pred=row['chronos_pred'],
                conformal_naive_pred=row['conformal_naive_pred'],
                transformer_pred=row['transformer_pred'],
                arima_pred = row['arima_pred'],
                xgb_pred=row['xgb_pred']
            ))
        
        # Batch insert in transaction
        with transaction.atomic():
            InfluenzaRecord.objects.bulk_create(records, batch_size=1000)
    else:
        for _, row in final_df.iterrows():
            records.append(RSVRecord(
                timestamp=row['timestamp'],
                organization=row['organization'],
                childrens_hospital=row['childrens_hospital'],
                admissions=row['admissions'],
                forecast=row['forecast'],
                chronos_pred=row['chronos_pred'],
                conformal_naive_pred=row['conformal_naive_pred'],
                transformer_pred=row['transformer_pred'],
                arima_pred = row['arima_pred'],
                xgb_pred=row['xgb_pred']
            ))
        
        # Batch insert in transaction
        with transaction.atomic():
            RSVRecord.objects.bulk_create(records, batch_size=1000)
    print(f"Successfully inserted {len(records)} records")