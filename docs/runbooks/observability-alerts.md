# Runbook — Booking API observability alerts

Use this runbook with the Prometheus rules in
`deploy/observability/prometheus/rules/booking-alerts.yml`. Record the alert start, first
notification, mitigation and resolved timestamps in the incident report.

## HighErrorRate

This alert fires when more than 5% of at least 100 requests in a one-minute window return an
HTTP 5xx response and the condition remains true for two minutes.

1. Open the Booking API overview dashboard with the alert time range.
2. Identify the affected route and the running `service_version`.
3. Open a representative error trace, then follow its trace ID to the correlated log.
4. Check the latest deployment and the fault-injection settings.
5. If the current release caused the errors, start the documented rollback workflow.
6. Confirm readiness, a successful booking smoke test and the alert's resolved state.

## ApiProbeDown

This alert fires after the independent blackbox probe has returned `probe_success = 0` for one
minute. It still works when the API process cannot emit HTTP metrics.

1. Check the backend container state and its readiness endpoint from the demo host.
2. Check PostgreSQL health because readiness depends on the database.
3. Inspect backend and proxy logs for the first failure in the alert window.
4. Restart a failed runtime dependency or roll back the current release as appropriate.
5. Confirm `probe_success = 1` and the alert's resolved state.

The probe runs on the same single VM as the service. It detects API, proxy and database
readiness failures, but cannot report a complete VM or network outage to an external receiver.

## HighLatencyP95

This warning fires when any route remains above 500 ms p95 latency for five minutes with at
least 100 requests in the same window.

1. Compare latency by route and inspect host/container CPU, memory and disk panels.
2. Open a slow trace to separate database time from application time.
3. Check whether latency fault injection is active and note its expiry time.
4. Remove the fault or roll back the release, then confirm p95 returns below 500 ms.
