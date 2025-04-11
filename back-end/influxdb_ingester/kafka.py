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



INFLUXDB_TOKEN="u9-rX6MNrziGfs2Fq6d4f9JNl_XWN6_DmxmciDtDUY9w8ehkgZxm9Axp4iuqUIhygsiEGC1tkPFtxt9h6G8hHg=="
INFLUXDB_ORG="Shiva"
INFLUXDB_URL="http://localhost:8086"
INFLUXDB_BUCKET="timeseriesprediction"


def send_to_kafka(topic, data):
    producer.send(topic, data)
    producer.flush()
    

    
def create_point(data) -> Point:
    """
    Create an InfluxDB point from a CSV row.
    
    Expected CSV columns:
      - ADMIT_DTS: timestamp
      - ORGANIZATION_NM, CHILDRENS_HOSPITAL: tags
      - EMPI, AGE_YEARS_NO, AGE_DAYS, REGION, REASON_FOR_VISIT, NURSE_UNIT_DSP, ICU_FLG: fields
    """
    point = Point(data["measurement"])
    
    try:
        timestamp = pd.to_datetime(data["timestamp"])
    except Exception as e:
        print("Error parsing timestamp for the patient having ID:", data["empi"], "Error:", e)
        return None
    point.time(timestamp, WritePrecision.S)
    
    toggleData = data["toggleData"]
    
    point.tag("ORGANIZATION_NM", str(data["hospital"]))
    point.tag("CHILDRENS_HOSPITAL", str(1 if toggleData["children"] else 0))

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


def safe_json_deserializer(message):
    try:
        decoded = message.decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        print(f"[Deserializer Error] Raw message: {message}")
        print(f"[Deserializer Error] Exception: {e}")
        return None
    

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
        value_deserializer=safe_json_deserializer)
    for msg in consumer:
        if msg is None:
            print("[Warning] Skipped empty or malformed message")
            continue
        data = msg.value
        print(f"[Consumer] Consumed: {data}")
        point = create_point(data)
        if point:
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
            print(f"[Consumer] Written to InfluxDB: {data}")
        else:
            print(f"Unable to create point for the data: {data}")
