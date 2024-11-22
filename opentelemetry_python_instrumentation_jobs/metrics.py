import functools
import logging
import os

from datetime import datetime

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from .fake_exporters import FakeMetricExporter

from .log_handler import otlp_handler

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(), otlp_handler])
logger = logging.getLogger("metrics-exporter")

SENDING_METRICS_ENABLED = os.getenv('SENDING_LOGS_AND_METRICS_ENABLED', 'false').lower() == 'true'

SERVICE_NAME = os.getenv('OTEL_SERVICE_NAME')
EXPORT_INTERVAL = int(os.getenv('OTEL_EXPORT_INTERVAL', '5000'))
METRIC_PREFIX = os.getenv('METRIC_PREFIX', 'test')
if SERVICE_NAME is None:
    raise Exception("OTEL_SERVICE_NAME is not set")
print(SERVICE_NAME)

if SENDING_METRICS_ENABLED:
    exporter = OTLPMetricExporter()
else:
    exporter = FakeMetricExporter()
    logger.warning("Sending metrics is disabled. Using FakeMetricExporter.")

reader = PeriodicExportingMetricReader(exporter, export_interval_millis=EXPORT_INTERVAL)
resource = Resource(attributes={"service.name": SERVICE_NAME})
metrics.set_meter_provider(MeterProvider(metric_readers=[reader], resource=resource))
meter = metrics.get_meter("job-metrics")

job_counter = meter.create_counter(
    name=f"{METRIC_PREFIX}_job_run_count",
    description="How many times the job has been run", unit="{count}"
)
status_counter = meter.create_counter(
    name=f"{METRIC_PREFIX}_job_status",
    description="Job counter by status (success, error)", unit="{count}",
)
duration_gauge = meter.create_gauge(
    name=f"{METRIC_PREFIX}_job_duration",
    description="Job execution duration in seconds", unit="s"
)
records_gauge = meter.create_gauge(
    name=f"{METRIC_PREFIX}_job_records",
    description="Number of records in job (processed, total)", unit="{count}"
)
last_status_gauge = meter.create_gauge(
    name=f"{METRIC_PREFIX}_job_last_status",
    description="Last job status (1, 0)", unit="{status}"
)
job_time_gauge = meter.create_gauge(
    name=f"{METRIC_PREFIX}_job_time",
    description="Job start and finish time in unix timestamp (started, finished)", unit="s"
)


def send_metrics(job_name: str, show_progress: bool = True):
    if not job_name:
        raise ValueError("job_name is required")

    if show_progress:
        from tqdm import tqdm

    def decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            logger.debug(f'job {job_name} started')
            processed_items = 0
            progress_bar = None
            if show_progress:
                progress_bar = tqdm(desc=f"{job_name} progress")

            def update_progress(progress, total):
                nonlocal processed_items
                processed_items += progress
                if show_progress:
                    progress_bar.total = total
                    progress_bar.refresh()
                    progress_bar.update(progress)
                records_gauge.set(processed_items, {"job_name": job_name, "type": "processed"})
                records_gauge.set(total, {"job_name": job_name, "type": "total"})

            start_time = datetime.now()
            job_time_gauge.set(int(start_time.timestamp()), {"job_name": job_name, "event": "started"})

            try:
                records_gauge.set(0, {"job_name": job_name, "type": "processed"})
                records_gauge.set(0, {"job_name": job_name, "type": "total"})

                # ===== job execution =====
                job_func(*args, job_name=job_name, update_progress=update_progress, **kwargs)
                # =========================

                status_counter.add(1, {"job_name": job_name, "status": "success"})
                last_status_gauge.set(1, {"job_name": job_name})
            except Exception as e:
                status_counter.add(1, {"job_name": job_name, "status": "error"})
                last_status_gauge.set(0, {"job_name": job_name})
                logger.error(str(e))
            finally:
                if progress_bar is not None:
                    progress_bar.close()
                job_counter.add(1, {"job_name": job_name})
                end_time = datetime.now()
                duration_gauge.set((end_time - start_time).seconds, {"job_name": job_name})
                job_time_gauge.set(int(datetime.now().timestamp()), {"job_name": job_name, "event": "finished"})
                logger.debug(f'job {job_name} finished')

        return wrapper

    return decorator
