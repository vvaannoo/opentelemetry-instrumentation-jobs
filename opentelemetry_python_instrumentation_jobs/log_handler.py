import os

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from .fake_exporters import FakeLogExporter

SENDING_METRICS_ENABLED = os.getenv('SENDING_LOGS_AND_METRICS_ENABLED', 'false').lower() == 'true'
SERVICE_NAME = os.getenv('OTEL_SERVICE_NAME', "unknown")

resource = Resource(attributes={"service.name": SERVICE_NAME})
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
if SENDING_METRICS_ENABLED:
    log_exporter = OTLPLogExporter()
else:
    log_exporter = FakeLogExporter()
    print('Using FakeLogExporter')

logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

otlp_handler = LoggingHandler(logger_provider=logger_provider)
