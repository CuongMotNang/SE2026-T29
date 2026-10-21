# Chạy stack local bằng Docker Compose

Hướng dẫn dựng toàn bộ stack (PostgreSQL, migration, Booking API) trên máy cá nhân bằng một lệnh, rồi kiểm tra giống như CI.

## Yêu cầu

- Docker Engine 24+ và Docker Compose v2 (`docker compose version`).
- Python 3.12 để chạy smoke test, persistence check và test (các script chỉ dùng thư viện chuẩn).
- Các port trống: `5432` (PostgreSQL) và `8000` (API). Có thể đổi bằng biến môi trường ở bảng bên dưới.

## Khởi động

Chạy từ thư mục gốc repository:

```bash
docker compose -f deploy/compose.yaml up -d --build --wait
```

Thứ tự khởi động:

1. `db` chạy và healthcheck `pg_isready` pass.
2. `migrate` chạy `alembic upgrade head` một lần rồi thoát với mã 0.
3. `backend` khởi động; healthcheck gọi `/health/ready` (chỉ pass khi bảng `appointments` đã tồn tại).

`--wait` chỉ trả về khi `backend` đã healthy. API ở `http://localhost:8000`, OpenAPI ở `http://localhost:8000/docs`.

## Kiểm tra giống CI

```bash
# Smoke test: readiness, /api/version, đặt rồi huỷ một lịch
python -m scripts.smoke_test --base-url http://localhost:8000

# E13: dữ liệu còn nguyên sau khi tạo lại container backend
python -m scripts.persistence_check seed --state-file /tmp/booking-e13.json
docker compose -f deploy/compose.yaml up -d --force-recreate --no-deps --wait backend
python -m scripts.persistence_check verify --state-file /tmp/booking-e13.json
```

## Dừng và dọn dẹp

```bash
docker compose -f deploy/compose.yaml down        # giữ dữ liệu trong volume
docker compose -f deploy/compose.yaml down -v     # XOÁ cả volume dữ liệu
```

Chỉ dùng `down -v` ở local. Không dùng trên máy demo vì lệnh này xoá booking.

## Chạy test

Unit test không cần database:

```bash
python -m pip install -e "./backend[dev]"
pytest backend/tests/unit
```

Integration test cần PostgreSQL riêng có tên database kết thúc bằng `_test`; xem [backend/README.md](../../backend/README.md).

## Biến môi trường

| Biến | Dùng ở | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `POSTGRES_USER` | Compose | `booking` | User PostgreSQL |
| `POSTGRES_PASSWORD` | Compose | `booking` | Mật khẩu PostgreSQL (chỉ dùng cho local) |
| `POSTGRES_DB` | Compose | `booking` | Tên database |
| `POSTGRES_PORT` | Compose | `5432` | Port PostgreSQL mở ra máy host |
| `BACKEND_PORT` | Compose | `8000` | Port API mở ra máy host |
| `BOOKING_DATABASE_URL` | API, Alembic | ghép từ các biến `POSTGRES_*` | URL kết nối async (`postgresql+asyncpg://...`) |
| `BOOKING_RELEASE` | API | `dev` | Tên release, trả về ở `/api/version` |
| `BOOKING_COMMIT_SHA` | API | `local` | Commit SHA, trả về ở `/api/version` |
| `BOOKING_DB_TIMEOUT_SECONDS` | API | `3.0` | Timeout kiểm tra DB của readiness (0–30 giây) |
| `TEST_DATABASE_URL` | pytest | — | Database cho integration test, tên phải kết thúc bằng `_test` |

Ví dụ khi máy đã có PostgreSQL chạy ở port 5432:

```bash
POSTGRES_PORT=55433 BACKEND_PORT=18000 docker compose -f deploy/compose.yaml up -d --build --wait
```

## Xử lý sự cố

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| `--wait` báo `backend` unhealthy | Migration lỗi hoặc DB chưa sẵn sàng | `docker compose -f deploy/compose.yaml logs migrate backend` |
| `port is already allocated` | Port 5432 hoặc 8000 đang được dùng | Đổi `POSTGRES_PORT` / `BACKEND_PORT` |
| Build treo ở `pip install`, `Temporary failure in name resolution` | Container không phân giải được DNS (hay gặp khi host dùng `systemd-resolved`) | Build bằng `docker build --network host -t booking-backend:local backend` rồi chạy `up --no-build`, hoặc đặt `"dns": ["1.1.1.1", "8.8.8.8"]` trong `/etc/docker/daemon.json` và restart Docker |
| Smoke test báo `409` | Slot 10:00 ngày mai đã có booking từ lần chạy trước chưa huỷ | Huỷ booking đó hoặc `down -v` để làm mới dữ liệu local |
