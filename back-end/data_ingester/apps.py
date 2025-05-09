from django.apps import AppConfig
from threading import Thread
import os

class InfluxdbIngesterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'influxdb_ingester'
    def ready(self):
        from .kafka import run_consumer

        # Prevent double thread execution in dev mode
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        print("Starting Kafka Consumer as a background thread...")
        consumer_thread = Thread(target=run_consumer, daemon=True)
        consumer_thread.start()
