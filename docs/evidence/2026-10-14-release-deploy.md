# Release, Deploy và Rollback — Kết quả kiểm chứng (TASK-005)

- **Ngày thực hiện**: 14/10/2026
- **Người phụ trách**: Nguyễn Việt Anh (23001827)
- **Mốc**: M4 — Release + Deploy
- **Môi trường**: Windows / Linux compatible, Python 3.12+, Docker Compose

---

## 1. Lệnh kiểm tra và kết quả

```powershell
python -m ruff check .
python -m ruff format --check .
$env:PYTHONPATH="..;backend"
python -m pytest tests/unit -v
python -m scripts.release_manifest validate --manifest docs/releases/v0.1.0.json
python -m scripts.deploy --dry-run --manifest docs/releases/v0.1.0.json
python -m scripts.rollback --dry-run --target-manifest docs/releases/v0.1.0.json
```

### Kết quả tổng quát
- **Ruff lint**: Pass (0 cảnh báo, 0 lỗi).
- **Ruff format**: Pass (100% tệp nguồn đã format chuẩn).
- **Pytest unit test suite**: **34 passed in 2.59s**.
- **CLI release manifest validation**: Pass.
- **Deploy & Rollback dry-run**: Pass với khả năng tự động dọn stale lock, chuẩn bị `.env.production` ghim digest sha256 và giữ nguyên volume database.

---

## 2. Chi tiết các tiêu chí kiểm chứng (Evidence Verification)

### E08: Định danh release truy vết được
- **Cơ chế**:
  - Tệp [release_manifest.py](../../scripts/release_manifest.py) định nghĩa cấu trúc manifest chuẩn, bắt buộc digest định dạng `sha256:<64-hex>` và nghiêm cấm sử dụng tag `:latest`.
  - Manifest tham chiếu [v0.1.0.json](../releases/v0.1.0.json) chứa tag `v0.1.0`, commit SHA `e0426ba69da49d4f2bd56718a0f7a6392d8dcae2`, digest backend và migration revision `20261007_0001`.
  - Endpoint [version.py](../../backend/app/api/version.py) trả về `release` và `commit_sha` được tiêm thông qua `Depends(get_settings)`.
- **Kiểm chứng**:
  - Test `test_e08_version_endpoint_matches_release_manifest`: Xác nhận `/api/version` khớp chính xác dữ liệu trong manifest.
  - Test `test_e08_release_manifest_traceability_to_image_spec`: Xác nhận tính truy vết từ tag -> commit SHA -> Docker image digest.

### E12: Deploy lỗi rollback được và dữ liệu được bảo toàn
- **Cơ chế**:
  - Bộ script [deploy.py](../../scripts/deploy.py) và [rollback.py](../../scripts/rollback.py) tích hợp khóa mutex [deploy_lock.py](../../scripts/deploy_lock.py) để ngăn chặn chạy deploy hoặc rollback đồng thời.
  - Tự động sao lưu manifest hiện tại sang `deploy/previous-manifest.json` trước khi triển khai release mới.
  - Chạy smoke test nghiệp vụ [smoke_test.py](../../scripts/smoke_test.py): kiểm tra `/health/ready`, `/api/version`, truy vấn slot, tạo booking và hủy booking.
  - Khi smoke test thất bại: tự động kích hoạt `trigger_auto_rollback` về release trước đó mà **không xóa PostgreSQL volume** (nghiêm cấm `docker compose down -v`).
- **Kiểm chứng**:
  - Test `test_deploy_and_rollback_manifest_history_flow`: Chu trình deploy v1 -> deploy v2 -> rollback v1 khôi phục đúng cấu hình release v1.
  - Test `test_deploy_auto_rollbacks_on_smoke_test_failure`: Mô phỏng deploy thất bại, hệ thống tự động rollback về release v1 thành công.
  - Test `test_e12_booking_data_preserved_across_simulated_rollback`: Booking tạo trước khi deploy được bảo toàn nguyên vẹn sau rollback.
  - Mục tiêu thời gian: Rollback hoàn tất trong **≤ 5 phút** (thực tế đo trên test: < 1 giây; demo script dry-run: 0.00s).

### E14: Release tương thích schema cũ (Cửa sổ Rollback)
- **Cơ chế**:
  - Ban hành tài liệu [migration-policy.md](../releases/migration-policy.md) quy định mô hình Expand / Contract: mọi cột mới trong cửa sổ rollback bắt buộc phải `nullable=True` hoặc có `server_default`.
- **Kiểm chứng**:
  - Test `test_e14_schema_backward_compatibility_during_rollback_window`: Xác nhận mã nguồn phiên bản rollback thực hiện đầy đủ các nghiệp vụ (xem slot, đặt lịch 201, xem danh sách 200, hủy lịch 204) trên database schema hiện tại mà không gặp lỗi.

---

## 3. Các artifact đã bàn giao trong TASK-005

1. **Docker packaging & Compose**:
   - [backend/Dockerfile](../../backend/Dockerfile): Container hóa Backend API với multi-stage, non-root user `appuser` (UID 10001) và health check.
   - [deploy/compose.production.yaml](../../deploy/compose.production.yaml): Compose production ghim image bằng digest, volume `postgres_data` bảo toàn dữ liệu.
   - [deploy/compose.yaml](../../deploy/compose.yaml): Compose phục vụ local dev.
2. **Scripts & Tooling**:
   - [scripts/release_manifest.py](../../scripts/release_manifest.py): Model manifest, schema validation, CLI `create` và `validate`.
   - [scripts/deploy_lock.py](../../scripts/deploy_lock.py): Khóa mutex chống chạy đồng thời, tự động phát hiện và dọn stale lock.
   - [scripts/smoke_test.py](../../scripts/smoke_test.py): Bộ smoke test tự động (readiness, version, slot, create & cancel booking).
   - [scripts/deploy.py](../../scripts/deploy.py) & [scripts/deploy.sh](../../scripts/deploy.sh): Orchestration deploy với digest, migrations, và auto-rollback.
   - [scripts/rollback.py](../../scripts/rollback.py) & [scripts/rollback.sh](../../scripts/rollback.sh): Khôi phục release trước đó an toàn, giữ nguyên volume DB.
3. **CI/CD Workflows**:
   - [.github/workflows/ci.yml](../../.github/workflows/ci.yml): Lint, unit tests, integration tests PostgreSQL, và Docker build checks.
   - [.github/workflows/release.yml](../../.github/workflows/release.yml): Trigger khi push Git tag `v*`, build và push image lên GHCR, tạo manifest JSON và GitHub Release.
   - [.github/workflows/rollback.yml](../../.github/workflows/rollback.yml): Workflow khôi phục phiên bản theo yêu cầu qua `workflow_dispatch`.
4. **Tài liệu & Chính sách**:
   - [docs/releases/v0.1.0.json](../releases/v0.1.0.json): Release manifest mẫu chuẩn.
   - [docs/releases/migration-policy.md](../releases/migration-policy.md): Quy định migration tương thích ngược.
5. **Bộ Test Suite**:
   - [backend/tests/unit/test_release_manifest.py](../../backend/tests/unit/test_release_manifest.py)
   - [backend/tests/unit/test_deploy_lock.py](../../backend/tests/unit/test_deploy_lock.py)
   - [backend/tests/unit/test_deploy_and_rollback.py](../../backend/tests/unit/test_deploy_and_rollback.py)
   - [backend/tests/unit/test_smoke_test.py](../../backend/tests/unit/test_smoke_test.py)
   - [backend/tests/unit/test_release_contract_e08.py](../../backend/tests/unit/test_release_contract_e08.py)
   - [backend/tests/integration/test_release_e08_e12_e14.py](../../backend/tests/integration/test_release_e08_e12_e14.py)
