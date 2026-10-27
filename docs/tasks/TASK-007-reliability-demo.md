# TASK-007 — Reliability demo và evidence

- Trạng thái: **In Progress**
- Người phụ trách: **Nguyễn Việt Anh (23001827)**
- Mốc: **M6 — Reliability demo**
- Phụ thuộc: TASK-005, TASK-006

## Mục tiêu

Chạy thử tải và incident drill để chứng minh khả năng phát hiện, điều tra và khôi phục hệ thống.

## Công việc

- Chuẩn bị load script và fault injection có thời hạn trên môi trường demo.
- Chạy tải tham chiếu 10 request/giây trong 10 phút và lưu điều kiện đo.
- Ghi timeline fault, alert, điều tra, rollback và phục hồi nghiệp vụ.
- Kiểm tra booking cũ còn nguyên sau rollback.
- Lưu test results, telemetry queries, release manifest và incident report.
- Cập nhật trạng thái E01–E16 bằng bằng chứng thực tế.

## Tiêu chí hoàn thành

- Báo cáo độ trễ ghi rõ môi trường, dữ liệu, phiên bản và khoảng đo.
- Alert firing trong mục tiêu đã định; tìm được trace/log và release gây lỗi.
- Rollback hoàn tất trong mục tiêu 5 phút, smoke test pass và dữ liệu còn nguyên.
- Incident report và toàn bộ link evidence cần thiết đã được lưu.
- Không mô tả hệ thống là “production-ready” nếu chưa đủ bằng chứng.

## Tiến độ tuần 2 — thứ Hai và thứ Ba (C081–C084)

- Hoàn thành luồng xem slot → đặt → hủy trong `loadtest/booking.js`; tách riêng `409`.
- Có profile mặc định 10 HTTP request/giây trong 10 phút, ngưỡng p95 < 500 ms
  cho từng route, lỗi < 1%, kiểm tra dropped iterations và các checks nghiệp vụ.
- Tự xuất summary JSON kèm cấu hình tải, release/SHA và điều kiện đo;
  hướng dẫn chạy tại [loadtest/README.md](../../loadtest/README.md).
- [Kiểm tra script ngày 27/10/2026](../evidence/loadtest/2026-10-27-week2-smoke.md):
  22 kiểm thử JavaScript, 85 unit tests, k6 inspect và smoke với PostgreSQL/API thật.
- **E15 vẫn chưa kiểm chứng**: smoke 15 giây chỉ xác nhận script hoạt động;
  phép đo 10 phút trên môi trường tham chiếu và incident drill còn lại trong TASK-007.
