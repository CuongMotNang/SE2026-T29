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
| Tasks | Backlog M0–M6 và tiêu chí hoàn thành | Team phân công owner và cập nhật trạng thái |
| Evidence | Bảng truy vết thiết kế → code → tests và tiêu chí kiểm chứng | Code, tests chạy thành công, pipeline, dashboard và incident thực nghiệm |

Repository hiện mới có tài liệu thiết kế, chưa có mã nguồn ứng dụng để kiểm tra. Bộ này không chứa ứng dụng chạy được và không khẳng định có test, deployment hoặc SLO đã đạt.

## Bước triển khai đầu tiên

Team xác nhận kiến trúc và phân công owner trong [Tasks](docs/tasks/README.md), rồi triển khai một lát cắt nhỏ: FastAPI → PostgreSQL → tạo/xem/hủy lịch → tests với PostgreSQL thật → React UI. Cấu trúc mã nguồn dự kiến nằm trong `docs/evidence.md`; các đường dẫn chưa được triển khai được ghi rõ là dự kiến.

Sau khi lát cắt này chạy được, thêm Docker, CI, release/deploy, telemetry và incident drill theo các mốc trong tài liệu Evidence.
