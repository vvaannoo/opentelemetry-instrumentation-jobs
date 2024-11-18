from typing import Sequence

from opentelemetry.sdk._logs import LogData
from opentelemetry.sdk._logs._internal.export import LogExporter
from opentelemetry.sdk.metrics._internal.export import MetricExporter
from opentelemetry.sdk.metrics._internal.point import MetricsData


class FakeMetricExporter(MetricExporter):
    def export(self, metrics: MetricsData, timeout_millis: float = 10_000, **kwargs) -> int:
        return 0  # Return code 0 indicates success

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        pass

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        pass


class FakeLogExporter(LogExporter):
    def export(self, batch: Sequence[LogData]):
        pass

    def shutdown(self):
        pass
