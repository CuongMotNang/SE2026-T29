# Load Testing — K6 Suite

Thư mục `loadtest/` chứa bộ công cụ và các kịch bản kiểm thử tải (Load Testing) bằng [k6](https://k6.io/) cho hệ thống Booking API, phục vụ kiểm chứng mốc **M6 — Reliability Demo** và chỉ số cam kết **E15** trong [Evidence](../docs/evidence.md).

---

## 1. Mục tiêu và tiêu chuẩn đánh giá (SLO & E15)

- **Cam kết E15:** Dưới mức tải tham chiếu 10 request/giây trong 10 phút, độ trễ p95 của các endpoint nghiệp vụ phải đạt dưới **500 ms**, tỷ lệ lỗi HTTP 5xx phải dưới **1%**.
- **Kịch bản kiểm thử:**
  - `slots.js`: Kiểm thử tải endpoint tra cứu khung giờ trống (`GET /api/slots`).
  - `booking.js`: Kịch bản tổng hợp mô phỏng người dùng tra cứu slot, đặt lịch hẹn và hủy lịch hẹn (phát triển trong Tuần 2 theo kế hoạch TASK-007).

---

## 2. Cấu trúc thư mục

```text
loadtest/
├── README.md         # Tài liệu hướng dẫn cấu hình và chạy thử tải
├── booking.js        # Kịch bản k6 tổng hợp quy trình tra cứu và đặt lịch
└── slots.js          # Kịch bản k6 kiểm thử endpoint tra cứu slot (/api/slots)
```

---

## 3. Cài đặt k6

### Cách 1: Cài đặt k6 CLI trực tiếp

- **Windows (winget):**
  ```powershell
  winget install k6 --source winget
  ```
- **Windows (Chocolatey):**
  ```powershell
  choco install k6
  ```
- **macOS (Homebrew):**
  ```bash
  brew install k6
  ```
- **Linux (Debian/Ubuntu):**
  ```bash
  sudo gpg -k
  sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
  echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
  sudo apt-get update && sudo apt-get install k6
  ```

### Cách 2: Sử dụng Docker container (không cần cài đặt CLI)

```bash
docker run --rm -i grafana/k6 run - < loadtest/slots.js
```

---

## 4. Các biến môi trường cấu hình

| Biến | Ý nghĩa | Mặc định | Ví dụ |
| --- | --- | --- | --- |
| `BASE_URL` | Địa chỉ gốc của Booking API | `http://localhost:8000` | `http://192.168.1.100:8000` |
| `TARGET_DATE` | Ngày cần tra cứu slot (`YYYY-MM-DD`) | Ngày mai (tính theo ngày hiện tại) | `2026-11-01` |
| `VUS` | Số lượng Virtual Users đồng thời | `5` | `10` |
| `DURATION` | Thời lượng chạy kịch bản | `30s` | `10m` |
| `TARGET_RPS` | Tần suất request mục tiêu (cho constant arrival) | `10` | `10` |

---

## 5. Hướng dẫn thực thi

### 5.1. Chạy nhanh kịch bản kiểm tra tra cứu slots (`slots.js`)

```bash
# Sử dụng CLI cục bộ
k6 run loadtest/slots.js

# Hoặc truyền biến môi trường tuỳ chỉnh
k6 run -e BASE_URL=http://localhost:8000 -e VUS=5 -e DURATION=30s loadtest/slots.js
```

### 5.2. Chạy qua Docker kết nối vào backend host

- **Windows / macOS (qua host.docker.internal):**
  ```bash
  docker run --rm -i -e BASE_URL=http://host.docker.internal:8000 grafana/k6 run - < loadtest/slots.js
  ```
- **Linux (qua host network):**
  ```bash
  docker run --rm -i --network=host -e BASE_URL=http://localhost:8000 grafana/k6 run - < loadtest/slots.js
  ```

### 5.3. Xuất kết quả tổng hợp (Summary JSON) để lưu evidence

```bash
k6 run --summary-export=reports/loadtest-slots-summary.json loadtest/slots.js
```

---

## 6. Tiêu chí kiểm tra trong kịch bản (Thresholds & Checks)

Mỗi kịch bản k6 tích hợp các ngưỡng kiểm tra chất lượng tự động:

- **HTTP Status Check:** Tất cả response phải trả về mã `200 OK`.
- **Response Format Check:** Dữ liệu trả về phải là mảng JSON hợp lệ chứa các slot có trường `starts_at`.
- **Threshold `http_req_duration`:** `p(95) < 500ms` (đáp ứng tiêu chí E15).
- **Threshold `http_req_failed`:** `rate < 0.01` (tỷ lệ request lỗi không vượt quá 1%).
