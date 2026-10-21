# TASK-006 — Observability và cảnh báo

- Trạng thái: **In Progress**
- Người phụ trách: **Vũ Thành Công**
- Phối hợp backend: **Phạm Minh Cương (23001840)**
- Mốc: **M5 — Observability**
- Phụ thuộc: TASK-004

## Mục tiêu

Thu thập metrics, traces và logs để phát hiện, điều tra lỗi và liên hệ lỗi với release.

## Công việc

- Instrument FastAPI bằng OpenTelemetry và export qua Collector.
- Cấu hình Prometheus, Tempo, Loki, Grafana và Alertmanager.
- Thêm correlation bằng trace ID, service version và release.
- Tạo dashboard cho request rate, error rate, latency và booking conflicts.
- Tạo alert cho tỷ lệ 5xx và blackbox readiness probe.
- Kiểm tra booking vẫn hoạt động khi Collector không sẵn sàng.

## Tiêu chí hoàn thành

- Từ một request lỗi có thể đi từ dashboard tới trace và log liên quan.
- Metric labels không chứa UUID, trace ID hoặc dữ liệu khách hàng.
- Probe phát hiện API ngừng đáp ứng ngay cả khi HTTP counter không tăng.
- Kiểm chứng E09–E11 và E16 trong [Evidence](../evidence.md) đạt.

## Tiến độ hiện tại

- Đã có instrumentation FastAPI/SQLAlchemy, span nghiệp vụ, metric booking conflict, JSON
  request log có trace correlation và OTLP exporter với queue/timeout hữu hạn.
- Đã có fault injection `error`/`latency` có tỷ lệ và thời điểm tự tắt, thực thi trước khi ghi DB.
- Còn thiếu Collector, Prometheus/Tempo/Loki/Grafana, dashboard, alert rules và evidence từ
  reliability drill trên môi trường demo; vì vậy task chưa thể chuyển sang `Done`.
