# TASK-002 — Xây dựng Booking API

- Trạng thái: **Done**
- Người phụ trách: **Phạm Minh Cương**
- Mốc: **M1 — Booking API**
- Phụ thuộc: TASK-001

## Mục tiêu

Xây dựng FastAPI và PostgreSQL cho luồng xem slot, tạo, xem và hủy booking.

## Công việc

- Tạo cấu trúc backend, cấu hình và kết nối PostgreSQL.
- Tạo migration cho bảng `appointments`, constraints và partial unique index.
- Cài đặt health, version, slots và appointments endpoints.
- Tách API, service, repository, model và domain errors theo module view.
- Viết unit tests và integration tests với PostgreSQL thật.

## Tiêu chí hoàn thành

- Các API chính trả đúng status và dữ liệu theo architecture context.
- Hai request đồng thời vào cùng slot cho kết quả một `201`, một `409`.
- Hủy có tính idempotent, giữ lịch sử và cho phép đặt lại slot.
- Các kiểm chứng E01–E05 trong [Evidence](../evidence.md) đạt.

## Kết quả

- Mã nguồn: commit `e1a7f4e`.
- Migration Alembic chạy thành công trên PostgreSQL 16.
- Ruff lint/format đạt; 21 unit và integration tests pass.
- Chi tiết: [Booking API test result](../evidence/2026-10-07-booking-api.md).
