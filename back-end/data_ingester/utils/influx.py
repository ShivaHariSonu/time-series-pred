import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def create_influx_client(url: str, token: str, org: str) -> InfluxDBClient:
    """
    Create and return an InfluxDBClient instance.
    """
    client = InfluxDBClient(url=url, token=token, org=org)
    return client

def create_bucket_if_not_exists(client: InfluxDBClient, bucket_name: str, org: str):
    """
    Create the specified bucket if it does not already exist.
    """
    buckets_api = client.buckets_api()
    bucket = buckets_api.find_bucket_by_name(bucket_name)
    if bucket is None:
        buckets_api.create_bucket(bucket_name=bucket_name, org=org)
        print(f"Bucket '{bucket_name}' created.")
    else:
        print(f"Bucket '{bucket_name}' already exists.")

def read_csv_data(file_path: str) -> pd.DataFrame:
    """
    Read CSV data from the provided file path.
    """
    df = pd.read_csv(file_path)
    return df

def create_point(row: pd.Series,measurement:str) -> Point:
    """
    Create an InfluxDB point from a CSV row.
    
    Expected CSV columns:
      - ADMIT_DTS: timestamp
      - ORGANIZATION_NM, CHILDRENS_HOSPITAL: tags
      - EMPI, AGE_YEARS_NO, AGE_DAYS, REGION, REASON_FOR_VISIT, NURSE_UNIT_DSP, ICU_FLG: fields
    """
    point = Point(measurement)
    
    # Parse the timestamp from ADMIT_DTS column (expected format: "YYYY-MM-DD HH:MM:SS")
    try:
        timestamp = pd.to_datetime(row["ADMIT_DTS"])
    except Exception as e:
        print("Error parsing timestamp for row:", row, "Error:", e)
        return None
    point.time(timestamp, WritePrecision.S)
    
    # Add tags (ensure they are strings)
    point.tag("ORGANIZATION_NM", str(row["ORGANIZATION_NM"]))
    point.tag("CHILDRENS_HOSPITAL", str(row["CHILDRENS_HOSPITAL"]))
    
    # Add fields
    try:
        point.field("EMPI", int(row["EMPI"]))
        point.field("AGE_YEARS_NO", int(row["AGE_YEARS_NO"]))
        point.field("AGE_DAYS", int(row["AGE_DAYS"]))
        point.field("REGION", str(row["REGION"]))
        point.field("REASON_FOR_VISIT", str(row["REASON_FOR_VISIT"]))
        point.field("NURSE_UNIT_DSP", str(row["NURSE_UNIT_DSP"]))
        point.field("ICU_FLG", int(row["ICU_FLG"]))
    except Exception as e:
        print("Error processing fields for row:", row, "Error:", e)
        return None

    return point

def ingest_data(client: InfluxDBClient, bucket: str, org: str, df: pd.DataFrame, measurement:str):
    """
    Ingest CSV data points into InfluxDB.
    """
    write_api = client.write_api(write_options=SYNCHRONOUS)
    for index, row in df.iterrows():
        point = create_point(row,measurement)
        if point:
            write_api.write(bucket, org, point)
            print(f"Written point for row {index}")
        else:
            print(f"Skipping row {index} due to errors.")
            
            
def query_data(client:InfluxDBClient, org: str,query:str):
    """
    Query data from INfluxDB
    """
    query_api = client.query_api()
    result = query_api.query_data_frame(query,org=org)
    if isinstance(result, list):
        df = pd.concat(result)
    else:
        df = result
    return df
    
    
