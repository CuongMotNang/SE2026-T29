# TASK-004 — Container hóa và CI

- Trạng thái: **In Progress**
- Người phụ trách: **Nguyễn Mai Hoàng Anh**
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

## Đồng bộ trạng thái ngày 25/10/2026

- Đã có Dockerfiles frontend/backend, Compose local, CI backend/frontend, E2E, build và smoke.
- E07/E13 đã có [bằng chứng GitHub/CI](../evidence/2026-10-21-container-ci.md); frontend có
  [kết quả local](../evidence/frontend/2026-10-25-task-003-local.md).
- Người phụ trách xác nhận CI trên commit tích hợp mới nhất trước khi chốt `Done`.

## Đồng bộ trạng thái ngày 28/10/2026 — CD lên máy demo

- Máy demo `booking-demo` (VM Multipass) có runner label `demo`; `deploy.yml` và `rollback.yml`
  chạy trên runner này, state ở `/opt/booking/state`. Xem [demo-host.md](../devops/demo-host.md).
- Release `v0.2.1` đã deploy qua pipeline, có duyệt ở environment `demo`; E08 đạt trên máy demo:
  [bằng chứng 28/10](../evidence/2026-10-28-e08-demo-deploy.md).
- Còn lại cho TASK-004: rollback qua `rollback.yml` trên máy demo cùng TASK-005/TASK-007, và deploy
  observability stack lên máy demo (lịch tuần 4).
