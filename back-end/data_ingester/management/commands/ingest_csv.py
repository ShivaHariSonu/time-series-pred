from django.core.management.base import BaseCommand
from django.conf import settings

from data_ingester.utils.influx import (
    create_influx_client,
    create_bucket_if_not_exists,
    read_csv_data,
    ingest_data
)

class Command(BaseCommand):
    help = 'Ingest CSV data into InfluxDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file_path',
            type=str,
            help='Path to the CSV file',
            required=True
        )
        parser.add_argument(
            '--measurement',
            type=str,
            help='Type of the file',
            required=True
        )
        
        

    def handle(self, *args, **options):
        conf = settings.INFLUXDB_SETTINGS
        influx_token = conf['token']
        influx_url = conf['url']
        influx_org = conf['org']
        bucket_name = conf['bucket']
        file_path = options['file_path']
        measurement = options['measurement']

        self.stdout.write("Starting ingestion process...")

        # Create InfluxDB client and ensure the bucket exists
        client = create_influx_client(influx_url, influx_token, influx_org)
        create_bucket_if_not_exists(client, bucket_name, influx_org)

        # Read CSV data and ingest into InfluxDB
        df = read_csv_data(file_path)
        ingest_data(client, bucket_name, influx_org, df, measurement)

        # Close the InfluxDB client
        client.close()
        self.stdout.write(self.style.SUCCESS("Data ingestion completed."))
