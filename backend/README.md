# Booking API

FastAPI backend cho dịch vụ đặt lịch. API dùng PostgreSQL để bảo vệ transaction và ngăn hai booking đang hoạt động dùng cùng một slot.

## Yêu cầu

- Python 3.12+
- PostgreSQL 18 hoặc tương thích

## Cài đặt

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[dev]"
```

Trên Linux hoặc macOS, dùng `source .venv/bin/activate` thay cho lệnh kích hoạt trên Windows.

Sao chép `.env.example` thành `.env` hoặc khai báo các biến môi trường tương ứng. Không commit file `.env`.

## Khởi tạo database và chạy API

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

API mặc định chạy tại `http://localhost:8000`; OpenAPI tại `/docs`.

## Chạy tests

Khởi động PostgreSQL test riêng:

```bash
docker compose -f compose.test.yaml up -d
```

Khai báo URL database test rồi chạy:

```bash
set TEST_DATABASE_URL=postgresql+asyncpg://booking:booking@localhost:55432/booking_test
pytest
```

Trên PowerShell, dùng `$env:TEST_DATABASE_URL=...`; trên Linux/macOS, dùng `export TEST_DATABASE_URL=...`.

Database integration test bắt buộc có tên kết thúc bằng `_test`. Test sẽ từ chối chạy nếu URL trỏ tới database khác.
