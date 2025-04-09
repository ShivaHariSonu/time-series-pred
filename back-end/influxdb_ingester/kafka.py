from kafka import KafkaProducer
from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point, WritePrecision
import json
from django.conf import settings
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'test',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    group_id='influx-consumer-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

conf = settings.INFLUXDB_SETTINGS
INFLUXDB_TOKEN = conf['token']
INFLUXDB_URL = conf['url']
INFLUXDB_ORG = conf['org']
INFLUXDB_BUCKET = conf['bucket']

def send_to_kafka(topic, data):
    producer.send(topic, data)
    producer.flush()
    

    
def create_point(raw_data:str) -> Point:
    """
    Create an InfluxDB point from a CSV row.
    
    Expected CSV columns:
      - ADMIT_DTS: timestamp
      - ORGANIZATION_NM, CHILDRENS_HOSPITAL: tags
      - EMPI, AGE_YEARS_NO, AGE_DAYS, REGION, REASON_FOR_VISIT, NURSE_UNIT_DSP, ICU_FLG: fields
    """
    data = json.loads(raw_data)
    point = Point(data["measurement"])
    
    try:
        timestamp = pd.to_datetime(data["timestamp"])
    except Exception as e:
        print("Error parsing timestamp for the patient having ID:", data["empi"], "Error:", e)
        return None
    point.time(timestamp, WritePrecision.S)
    
    toggleDataString = data["toggleData"]
    
    toggleData = json.loads(toggleDataString)
    
    # Add tags (ensure they are strings)
    point.tag("ORGANIZATION_NM", str(data["hospital"]))
    point.tag("CHILDRENS_HOSPITAL", str(1 if toggleData["children"] else 0))
    
    # Add fields
    try:
        point.field("EMPI", int(data["empi"]))
        point.field("AGE_YEARS_NO", int(data["ageyearsno"]))
        point.field("AGE_DAYS", int(data["agedays"]))
        point.field("REGION", str(data["region"]))
        point.field("REASON_FOR_VISIT", str(data["reasonforvisit"]))
        point.field("NURSE_UNIT_DSP", str(data["nurseunitdsp"]))
        point.field("ICU_FLG", int(1 if toggleData["icuflag"] else 0))
    except Exception as e:
        print("Error processing fields for the patient having ID:", data["empi"], "Error:", e)
        return None

    return point


    
def run_consumer():
    print("Starting Kafka Consumer Thread...")
    influx_client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    consumer = KafkaConsumer(
        'test',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        group_id='influx-consumer-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    #TBD :- Based on Input from the kafka need to update the point
    for msg in consumer:
        data = msg.value
        print(f"[Consumer] Consumed: {data}")
        
        point = create_point(data)
        if point:
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
            print(f"[Consumer] Written to InfluxDB: {data}")
        else:
            print(f"Unable to create point for the data: {data}")
