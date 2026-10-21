# Container và CI — Kết quả kiểm chứng (TASK-004, tuần 1)

- **Ngày thực hiện**: 21/10/2026
- **Người phụ trách**: Nguyễn Mai Hoàng Anh (23001824)
- **Mốc**: M3 — Container + CI
- **Pull request**: [#4](https://github.com/CuongMotNang/SE2026-T29/pull/4)
- **CI run**: [39541589590](https://github.com/CuongMotNang/SE2026-T29/actions/runs/39541589590), commit `e47fa29`, runner `ubuntu-latest`

## 1. Kết quả CI

| Job | Kết quả | Thời gian |
| --- | --- | --- |
| Lint and Format Checks | Pass | 8 s |
| Backend Unit and Integration Tests (PostgreSQL 16) | Pass | 37 s |
| Compose Stack Smoke Test | Pass | 44 s |
| Docker Build Verification + Trivy | Pass (report only) | 52 s |

## 2. E13 — Dữ liệu tồn tại qua recreate

Job `compose-smoke` chạy `deploy/compose.yaml` với `postgres:16-alpine`:

```text
Container booking-ci-db-1       Healthy
Container booking-ci-migrate-1  Exited (0)
Container booking-ci-backend-1  Healthy
[PASS] readiness_check: Application is ready (HTTP 200 after 0.02s).
[PASS] version_check: Version verified: release='ci', commit='e47fa295224670fcfb63f1a7e23ed47445059555'
[PASS] business_flow: Business smoke test passed: slots queried, booking created and cancelled.
[PASS] seed: Seeded booking 2b1c5b07-842a-4a81-8d09-fcf247137a71 at 2026-10-23T00:00:00+07:00
Container booking-ci-backend-1  Healthy        # sau docker compose up --force-recreate --no-deps backend
[PASS] verify: Booking 2b1c5b07-842a-4a81-8d09-fcf247137a71 survived recreate
```

Kiểm chứng thêm ở local (21/10/2026, Docker 29.8.1, Compose v5.5.1, `postgres:17-alpine` qua file override vì mạng máy local không tải được image 16):

- Container ID backend đổi từ `b6166e694426` sang `2fdc3c4ceef4` sau recreate; booking seed vẫn ở trạng thái `booked`.
- `verify` với ID không tồn tại trả `[FAIL] ... not found` và exit code 1, nên bước kiểm tra không pass giả.

**Kết luận E13:** Đạt trên CI.

## 3. Trivy scan image backend

Scan `HIGH,CRITICAL`, bỏ qua lỗ hổng chưa có bản vá. OS packages: 0. Python packages: 4 HIGH, 0 CRITICAL.

| Thư viện | Lỗ hổng | Bản đang dùng | Bản đã vá |
| --- | --- | --- | --- |
| msgpack | GHSA-6v7p-g79w-8964 | 1.1.2 | 1.2.1 |
| setuptools | CVE-2025-47273 | 70.3.0 | 78.1.1 |
| urllib3 | CVE-2026-97687 | 2.7.0 | 2.8.0 |
| urllib3 | CVE-2026-97689 | 2.7.0 | 2.8.0 |

Scan đang ở chế độ chỉ báo cáo. Việc nâng cấp các gói này và chuyển Trivy sang chặn build với `CRITICAL` nằm trong kế hoạch tuần 5.

## 4. Chưa kiểm chứng

- **E07** — một PR cố ý fail bị chặn merge: cần bật branch protection cho `main` (bắt buộc các check của `ci.yml` pass). Người thực hiện cần quyền admin repository; tài khoản hiện tại chỉ có quyền push.
