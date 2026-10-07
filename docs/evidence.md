# Evidence — Đối chiếu thiết kế, code và tests

Trạng thái ngày 07/10/2026: **mới có tài liệu thiết kế; chưa có mã nguồn ứng dụng để kiểm chứng**. Tên file/test dưới đây là dự kiến. Khi triển khai, thay đường dẫn bằng đường dẫn thực và điền link kết quả; không đánh dấu hoàn tất chỉ vì tên file đã tồn tại.

## 1. Cấu trúc repository dự kiến

| Nhóm | Các đường dẫn chính cần tạo | Liên hệ thiết kế |
| --- | --- | --- |
| Frontend | `frontend/src/pages/BookingPage.tsx`, `frontend/src/components/`, `frontend/src/api/appointments.ts` | UI và HTTP client trong module view |
| Bootstrap/API | `backend/app/main.py`, `config.py`, `api/appointments.py`, `api/health.py`, `api/version.py`, `api/slots.py`, `schemas/appointment.py` | Hợp đồng API và wiring |
| Business/data | `backend/app/services/booking.py`, `repositories/appointments.py`, `models/appointment.py`, `db.py`, `domain/errors.py` | Hướng API → service → repository → DB |
| Migrations | `backend/alembic/versions/` | Transaction/schema, uniqueness của active booking |
| Telemetry | `backend/app/telemetry/` | HTTP metrics, spans, log correlation |
| Tests | `backend/tests/unit/`, `backend/tests/integration/`, `frontend/tests/`, `tests/e2e/`, `tests/load/` | Kiểm chứng quy tắc và hệ thống |
| Container/deploy | `frontend/Dockerfile`, `backend/Dockerfile`, `deploy/compose.yaml`, `deploy/compose.production.yaml` | ADR-001 và runtime services |
| CI/CD | `.github/workflows/ci.yml`, `release.yml`, `rollback.yml`, `scripts/deploy.sh`, `scripts/rollback.sh` | Gates, release manifest và recovery |
| Observability | `observability/collector/`, `prometheus/`, `blackbox/`, `grafana/`, `tempo/`, `loki/`, `alertmanager/` | Telemetry routing và alert |
| Tài liệu vận hành | `docs/runbook.md`, `docs/incidents/`, `docs/releases/` | Quy trình drill, dữ liệu sự cố và định danh release |

Các đường dẫn backend viết ngắn ở cùng hàng được hiểu là nằm dưới `backend/app/`; workflow nằm dưới `.github/workflows/`. Repository thực tế có thể khác nếu team cập nhật module view và bảng đối chiếu cùng lúc.

## 2. Bảng truy vết thiết kế → bằng chứng

| ID | Cam kết thiết kế | Code/config dự kiến | Test hoặc thực nghiệm cần có | Tiêu chí pass | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| E01 | API đáp ứng và readiness phản ánh DB | `api/health.py` | `test_liveness_without_db`, `test_readiness_when_db_unavailable` | Live 200; DB lỗi thì ready 503 với timeout hữu hạn | Chưa kiểm chứng |
| E02 | Tạo booking lưu bền vững | Service, repository, model | `test_create_booking_persists` với PostgreSQL | 201; đọc lại đúng dữ liệu sau commit | Chưa kiểm chứng |
| E03 | Không đặt trùng slot đồng thời | Partial unique index + lỗi domain | `test_concurrent_booking_same_slot` | Hai request độc lập: một 201, một 409; đúng một active row | Chưa kiểm chứng |
| E04 | Slot đúng quy tắc và timezone | Schema/service | `test_invalid_slot`, `test_past_slot`, `test_timezone_normalization` | Từ chối slot sai; cùng thời điểm ở hai offset quy về cùng slot | Chưa kiểm chứng |
| E05 | Hủy giữ lịch sử và cho đặt lại | Service/repository | `test_cancel_is_idempotent`, `test_rebook_cancelled_slot`, `test_cancel_unknown_id` | 204 khi hủy/lặp lại; bản ghi cancelled còn; đặt lại 201; ID lạ 404 | Chưa kiểm chứng |
| E06 | UI phản ánh response thật | BookingPage + HTTP client | Frontend tests và E2E | Loading/error/success đúng; 409 không hiển thị thành công | Chưa kiểm chứng |
| E07 | Lỗi code chặn phát hành | `ci.yml`, `release.yml` | Một PR cố ý fail test ở branch demo | CI fail; không deploy qua pipeline chuẩn | Chưa kiểm chứng |
| E08 | Định danh release truy vết được | Manifest + `/api/version` | So tag/SHA/digest với deployment | Version API khớp manifest và images đang chạy | Chưa kiểm chứng |
| E09 | Telemetry chỉ ra request lỗi | Instrumentation + collector pipelines | Request fault rồi query backend telemetry | Có metrics, trace, log cùng trace ID và release | Chưa kiểm chứng |
| E10 | Telemetry lỗi không chặn booking | SDK timeout/batch | `test_booking_when_collector_unavailable` hoặc drill | Booking vẫn thành công; không chờ export vô hạn | Chưa kiểm chứng |
| E11 | Alert hoạt động dưới tải | Prometheus rules + Alertmanager | Fault injection có timestamp | Firing trong mục tiêu 3 phút; resolved sau phục hồi/cửa sổ đánh giá | Chưa kiểm chứng |
| E12 | Deploy lỗi rollback được | Deploy/rollback scripts + smoke tests | Release drill lỗi rồi khôi phục | ≤5 phút; version cũ; smoke test pass; booking cũ còn | Chưa kiểm chứng |
| E13 | Dữ liệu tồn tại qua recreate | PostgreSQL volume | Tạo booking, recreate API rồi đọc lại | Row không mất | Chưa kiểm chứng |
| E14 | Release tương thích schema cũ | Alembic + migration review | Chạy code bản rollback với schema sau migration | Tạo/xem/hủy đều pass | Chưa kiểm chứng |
| E15 | Độ trễ đạt mục tiêu tham chiếu | Load script + histogram | 10 request/giây, 10 phút, recording | ≥95% dưới 500 ms; báo đủ VM/dataset/phiên bản | Chưa kiểm chứng |
| E16 | API chết vẫn được phát hiện | Blackbox probe + alert rule | Stop API trong môi trường drill | Probe fail, alert xuất hiện dù HTTP counter không tăng | Chưa kiểm chứng |

Test E03 dùng hai kết nối/transaction độc lập được khởi động đồng thời và lặp có kiểm soát. Gọi tuần tự hai lần chỉ kiểm chứng duplicate booking thông thường. SQLite/in-memory fake không chứng minh hành vi partial index/concurrency của PostgreSQL.

Unit tests tập trung vào quy tắc nghiệp vụ. Integration tests kiểm chứng transaction, uniqueness và API contract. E2E kiểm chứng UI → API → DB. Load/drill kiểm chứng hành vi chất lượng; chúng bổ sung cho functional tests.

## 3. Kiểm tra code có đúng module view

- Routes gọi service, không chứa SQL/commit trực tiếp.
- Service không import React hoặc FastAPI HTTP response.
- Repository không trả HTTP response và không nhầm mọi lỗi DB thành conflict.
- Migration tạo đúng constraints được code dựa vào.
- Workflows dùng đúng image/config được tài liệu runtime mô tả.

Ghi kết quả review hoặc thêm kiểm tra dependency khi cần. Việc có thư mục tên `services` chưa chứng minh trách nhiệm đã được tách đúng.

## 4. Bằng chứng lưu khi thực nghiệm

| Bằng chứng | Vị trí dự kiến | Nội dung tối thiểu |
| --- | --- | --- |
| Test results | CI artifacts và link trong file này | Commit SHA, command, số pass/fail, DB thực dùng |
| Pipeline history | Link GitHub Actions runs | Run thành công và fail, commit, release, thời gian |
| Release manifest | `docs/releases/<release>.json` hoặc release artifact | Git tag, SHA, frontend/backend digests, config revision, migration revision |
| SLO/load report | `docs/evidence/slo-demo.md` | Cửa sổ đo, denominator/filter, request count, latency, môi trường |
| Telemetry screenshots/queries | `docs/evidence/observability/` | Time range, release, query, trace/log correlation |
| Incident report | `docs/incidents/<date>-booking-drill.md` | Timeline, impact, detection, cause, mitigation, follow-up |
| Rollback result | Workflow artifact + incident report | Bản trước/sau, duration, smoke result, data verification |

Ảnh dashboard một thời điểm không chứng minh SLO 30 ngày. Báo cáo demo phải dùng đúng khoảng thời gian đã đo và phân biệt mục tiêu với kết quả.

## 5. Mẫu incident report để điền sau drill

- **ID và ngày:** chưa thực nghiệm.
- **Môi trường / commit / release / digest:** …
- **Fault:** mô tả cấu hình và thời hạn.
- **Timeline:** deploy → fault start → alert firing → điều tra → rollback start/end → business recovery → alert resolved.
- **Impact:** số request lỗi / tổng request đủ điều kiện, số booking thất bại và khoảng thời gian.
- **Detection:** alert rule và link evidence.
- **Root cause:** fault được tiêm vào vị trí nào; trace/log nào chứng minh.
- **Resolution:** manifest được khôi phục, smoke result và dữ liệu trước/sau.
- **Follow-up:** thay đổi cụ thể, owner do team phân công, thời hạn.

## 6. Mốc triển khai và điều kiện hoàn thành

| Mốc | Làm gì | Hoàn thành khi |
| --- | --- | --- |
| M0 — Architecture | Xác nhận context/views/ADR | Team chốt giả định; ADR chuyển Accepted khi đồng ý |
| M1 — Booking API | DB migration, health, slots, tạo/xem/hủy; tests E01–E05 | API và tests PostgreSQL pass |
| M2 — UI | React form/list và xử lý lỗi | E2E tạo/hủy booking pass |
| M3 — Container + CI | Dockerfiles, Compose, kiểm tra PR | Local stack chạy; test fail chặn pipeline chuẩn |
| M4 — Release + Deploy | Registry, manifest, version endpoint, smoke và rollback | Deploy và khôi phục đúng release/digest được chứng minh |
| M5 — Observability | Metrics/traces/logs, dashboard, SLI và alert | Tìm được request lỗi xuyên telemetry; probe outage hoạt động |
| M6 — Reliability demo | Tải, fault, điều tra, rollback, incident | Có kết quả đo và bộ evidence theo bảng |

Tag các mốc hoàn thành bằng phiên bản tăng dần nếu cần, ví dụ `v0.1.0`, `v0.2.0`. Trước 1.0, API còn có thể thay đổi; document rõ. Chỉ công bố `v1.0.0` khi scope lab và bằng chứng đã đủ, kèm giới hạn single-VM. Không gắn nhãn “production-ready” chỉ dựa vào có Docker/CI.
