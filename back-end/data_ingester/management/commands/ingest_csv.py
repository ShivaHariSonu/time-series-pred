from django.core.management.base import BaseCommand
from django.conf import settings

from data_ingester.utils.postgres import (
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
            '--disease',
            type=str,
            help='Type of the disease',
            required=True
        )
        
        

    def handle(self, *args, **options):

        self.stdout.write("Starting ingestion process...")
        file_path = options['file_path']
        disease = options['disease']

        df = read_csv_data(file_path)
        ingest_data(df,disease)
        self.stdout.write(self.style.SUCCESS("Data ingestion completed."))
