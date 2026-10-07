# TASK-004 — Container hóa và CI

- Trạng thái: **Todo**
- Người phụ trách: **Chưa phân công**
- Mốc: **M3 — Container + CI**
- Phụ thuộc: TASK-002, TASK-003

## Mục tiêu

Đóng gói ứng dụng và tạo kiểm tra tự động để thay đổi lỗi không đi qua pipeline chuẩn.

## Công việc

- Viết Dockerfile cho frontend và backend.
- Tạo Docker Compose cho môi trường local.
- Tạo GitHub Actions chạy lint, backend tests, frontend tests và build checks.
- Dùng PostgreSQL thật cho integration tests trong CI.
- Ghi lại hướng dẫn chạy local và các biến môi trường cần thiết.

## Tiêu chí hoàn thành

- Stack local khởi động được bằng Docker Compose và vượt qua smoke test.
- CI chạy tự động trên pull request.
- Một test cố ý lỗi làm workflow fail và ngăn pipeline chuẩn tiếp tục.
- Kiểm chứng E07 và E13 trong [Evidence](../evidence.md) đạt.
