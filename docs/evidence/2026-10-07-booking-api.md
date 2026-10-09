# Booking API — Kết quả kiểm chứng cục bộ

- Ngày: 07/10/2026
- Commit mã nguồn được kiểm tra: `e0426ba`
- Môi trường: Windows, Python 3.12.14, PostgreSQL 16
- Database: PostgreSQL test tạm thời, database `booking_test`, port riêng `55432`

## Lệnh kiểm tra

```powershell
python -m ruff check .
python -m ruff format --check .
alembic upgrade head
$env:TEST_DATABASE_URL='postgresql+asyncpg://booking@127.0.0.1:55432/booking_test'
python -m pytest -q
```

## Kết quả

- Ruff lint: pass.
- Ruff format: pass.
- Alembic migration `20261007_0001`: pass.
- Pytest: **21 passed**.
- Test database được tạo riêng; fixture từ chối database không có hậu tố `_test`.

## Phạm vi đã kiểm chứng

- E01: liveness không phụ thuộc database; readiness trả `503` khi database không sẵn sàng.
- E02: tạo booking trả `201` và dữ liệu tồn tại sau commit.
- E03: hai request đồng thời vào cùng slot cho đúng một `201`, một `409` và một active row.
- E04: từ chối thời gian quá khứ/sai biên 30 phút/thiếu offset; chuẩn hóa UTC đúng.
- E05: hủy idempotent, giữ bản ghi cancelled, đặt lại slot được và ID lạ trả `404`.

## Giới hạn

Đây là kết quả cục bộ, chưa phải GitHub Actions artifact hoặc bằng chứng từ môi trường deployment. CI cần chạy lại cùng test suite với PostgreSQL service trước khi dùng kết quả làm release gate.
