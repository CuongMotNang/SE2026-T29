# Fault injection và backend observability — Kết quả kiểm chứng cục bộ

- **Ngày:** 21/10/2026
- **Phạm vi:** phần backend do Phạm Minh Cương (23001840) phụ trách
- **Mốc liên quan:** M5 — Observability và M6 — Reliability demo
- **Giới hạn:** chưa chạy Collector, Prometheus, Tempo, Loki, Grafana hoặc alert trên máy demo

## Phần đã triển khai

- Fault injection trước thao tác ghi DB với mode `error` hoặc `latency`, tỷ lệ chọn request,
  thời hạn bắt buộc và thời gian trễ cấu hình.
- Log request JSON ra stdout theo route template, không đọc body/query hoặc dữ liệu khách hàng.
- OpenTelemetry cho FastAPI, SQLAlchemy và request logging; export traces, metrics và logs qua
  OTLP/gRPC. URL/query có dữ liệu động được loại khỏi server spans.
- Span nghiệp vụ `booking.create`, `booking.cancel` và counter `booking_conflicts_total`.
- Resource attributes gồm service, release, commit SHA và deployment environment.
- Batch queue hữu hạn và timeout export để Collector lỗi không chặn luồng booking.

## Lệnh kiểm chứng

```powershell
cd backend
.venv\Scripts\python.exe -m ruff check . ..\scripts
.venv\Scripts\python.exe -m ruff format --check . ..\scripts
.venv\Scripts\python.exe -m pytest tests\unit -q
$env:TEST_DATABASE_URL='postgresql+asyncpg://booking:booking@127.0.0.1:55432/booking_test'
.venv\Scripts\python.exe -m pytest tests\integration -q
docker compose -f ..\deploy\compose.yaml config
docker compose -f ..\deploy\compose.production.yaml config
```

## Kết quả

- Unit tests: **55 passed**.
- Integration tests PostgreSQL 16: **14 passed**, gồm kiểm chứng mode `error` trả 500 và không
  tạo row trong database.
- Toàn bộ backend: **69 passed**.
- Ruff lint và format: **đạt**.
- Cả hai cấu hình Docker Compose: **hợp lệ**.
- Test batch isolation dùng span exporter cố ý block/fail trong một giây; thao tác tạo booking
  vẫn hoàn thành trước ngưỡng 500 ms cục bộ vì export chạy trên batch worker. Đây là mô phỏng
  exporter lỗi, chưa thay thế drill mất kết nối Collector thật.

## Trạng thái evidence

- **E09:** request FastAPI thật trong test tạo server trace và request log có cùng native trace/span
  ID; metric dùng cùng resource release. Chưa đạt end-to-end cho tới khi lưu query/ảnh từ
  Collector và telemetry backend thật.
- **E10:** đạt ở mức batch-isolation cục bộ; cần lặp lại với Collector mất kết nối trong môi trường
  demo.
- **E11:** fault injector đã sẵn sàng cho drill; alert firing/resolved vẫn chưa được kiểm chứng.
