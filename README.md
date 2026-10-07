# Production Readiness Lab — Bộ tài liệu kiến trúc

Trạng thái: thiết kế đề xuất để triển khai.

Đây là bộ tài liệu cho dịch vụ đặt lịch nhỏ, hướng tới trình diễn CI/CD, container, quan sát hệ thống, cảnh báo và rollback. Tài liệu gồm kiến trúc, kế hoạch task và bảng đối chiếu thiết kế với repository/tests.

## Đọc theo thứ tự

1. [Architecture](docs/architecture/README.md): mục lục tài liệu kiến trúc và quyết định kỹ thuật.
2. [Architecture context](docs/architecture/architecture-context.md): người dùng, phạm vi, ràng buộc và mục tiêu chất lượng.
3. [Module view](docs/architecture/module-view.md): các module mã nguồn, trách nhiệm và hướng phụ thuộc.
4. [Runtime view](docs/architecture/runtime-view.md): luồng request, telemetry, release và rollback.
5. [ADR-001](docs/architecture/adr/001-use-docker-compose.md): lựa chọn Docker Compose trên một VM, các phương án và đánh đổi.
6. [Tasks](docs/tasks/README.md): backlog triển khai, phụ thuộc và tiêu chí hoàn thành.
7. [Evidence](docs/evidence.md): cấu trúc repository dự kiến, test cần có và bằng chứng cần thu thập.

Các sơ đồ dùng Mermaid và có thể xem khi mở Markdown trên GitHub.

## Trạng thái thực tế

| Mục | Đã có trong bộ này | Chưa hoàn thành |
| --- | --- | --- |
| Architecture context | Tài liệu thiết kế | Team xác nhận các giả định |
| Two views | Hai tài liệu và sơ đồ | Đối chiếu với code sau khi triển khai |
| One ADR | ADR đầy đủ, trạng thái Proposed | Team chấp nhận quyết định |
| Booking API | FastAPI, PostgreSQL, Alembic; 21 tests pass cục bộ | CI và kiểm chứng trên môi trường dùng chung |
| Tasks | Backlog M0–M6; TASK-002 hoàn thành | Team phân công owner cho các task còn lại |
| Evidence | Bảng truy vết và kết quả E01–E05 cục bộ | Pipeline, dashboard và incident thực nghiệm |

Repository hiện có tài liệu thiết kế và Booking API backend. Chưa có React UI, deployment, observability hoặc kết quả SLO; kết quả test hiện tại mới được kiểm chứng cục bộ với PostgreSQL 16.

## Bước tiếp theo

Team xác nhận kiến trúc và phân công owner trong [Tasks](docs/tasks/README.md), sau đó triển khai [TASK-003 — React UI](docs/tasks/TASK-003-react-ui.md) trên Booking API đã có. Cấu trúc mã nguồn và trạng thái kiểm chứng nằm trong `docs/evidence.md`.

Sau khi UI chạy được, thêm container, CI, release/deploy, telemetry và incident drill theo các mốc trong tài liệu Evidence.
