# TASK-005 — Release, deploy và rollback

- Trạng thái: **Todo**
- Người phụ trách: **Nguyễn Việt Anh**
- Mốc: **M4 — Release + Deploy**
- Phụ thuộc: TASK-004

## Mục tiêu

Phát hành image có định danh, triển khai đúng artifact và khôi phục được phiên bản tốt trước đó.

## Công việc

- Tạo release workflow build và push image từ Git tag.
- Tạo release manifest chứa tag, commit SHA, image digests và migration revision.
- Viết deploy và rollback scripts có khóa chống chạy đồng thời.
- Thêm readiness timeout và smoke test nghiệp vụ sau deploy.
- Quy định migration tương thích với cửa sổ rollback.

## Tiêu chí hoàn thành

- `/api/version`, manifest và image đang chạy chỉ cùng một release.
- Deploy dùng image digest, không build lại trên VM và không dùng `latest`.
- Deploy lỗi tự khôi phục manifest trước đó và giữ nguyên booking cũ.
- Kiểm chứng E08, E12 và E14 trong [Evidence](../evidence.md) đạt.
