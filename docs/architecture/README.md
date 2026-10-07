# Architecture

Thư mục này mô tả kiến trúc đề xuất của Production Readiness Lab. Các tài liệu phản ánh thiết kế hiện tại; những nội dung chưa được kiểm chứng thực nghiệm vẫn được ghi rõ là mục tiêu hoặc giả định.

## Tài liệu

1. [Architecture context](architecture-context.md) — phạm vi, người dùng, ràng buộc, API và mục tiêu chất lượng.
2. [Module view](module-view.md) — cấu trúc mã nguồn, trách nhiệm và hướng phụ thuộc.
3. [Runtime view](runtime-view.md) — các thành phần khi chạy, luồng request, telemetry, deploy và rollback.
4. [ADR-001](adr/001-use-docker-compose.md) — quyết định đề xuất dùng Docker Compose trên một Linux VM.

## Quy tắc cập nhật

- Cập nhật tài liệu kiến trúc cùng pull request khi code hoặc cấu hình làm thay đổi thiết kế.
- Tạo ADR mới cho quyết định quan trọng; không xóa ADR cũ khi quyết định bị thay thế.
- Dùng trạng thái `Proposed`, `Accepted`, `Deprecated` hoặc `Superseded` cho ADR.
- Liên kết thay đổi với [task](../tasks/README.md) và cập nhật [Evidence](../evidence.md) khi đã có kết quả kiểm chứng.
