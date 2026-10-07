# TASK-007 — Reliability demo và evidence

- Trạng thái: **Todo**
- Người phụ trách: **Chưa phân công**
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
