from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelemetryConfig:
    """Runtime settings for a bounded, non-blocking telemetry pipeline."""

    enabled: bool = False
    service_name: str = "booking-api"
    release: str = "dev"
    deployment_environment: str = "local"
    commit_sha: str = "unknown"
    otlp_endpoint: str = "http://otel-collector:4317"
    otlp_insecure: bool = True
    exporter_timeout_millis: int = 2_000
    max_queue_size: int = 512
    max_export_batch_size: int = 64
    schedule_delay_millis: int = 1_000
    metric_export_interval_millis: int = 10_000
    export_logs: bool = True

    def __post_init__(self) -> None:
        positive_values = {
            "exporter_timeout_millis": self.exporter_timeout_millis,
            "max_queue_size": self.max_queue_size,
            "max_export_batch_size": self.max_export_batch_size,
            "schedule_delay_millis": self.schedule_delay_millis,
            "metric_export_interval_millis": self.metric_export_interval_millis,
        }
        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.max_export_batch_size > self.max_queue_size:
            raise ValueError("max_export_batch_size cannot exceed max_queue_size")

    @property
    def resource_attributes(self) -> dict[str, str]:
        """Stable, low-cardinality attributes shared by every telemetry signal."""

        return {
            "service.name": self.service_name,
            "service.version": self.release,
            # Keep the assignment's spelling and the current semantic-convention spelling.
            "deployment.environment": self.deployment_environment,
            "deployment.environment.name": self.deployment_environment,
            "release": self.release,
            "commit_sha": self.commit_sha,
        }
