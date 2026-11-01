# HƯỚNG DẪN TRIỂN KHAI VẬN HÀNH (DEPLOYMENT & OPERATIONS GUIDE)
**Dự án:** Hệ thống Quản trị Trung tâm Tiếng Anh (English Center Management System)  
**Phiên bản:** v1.0.0 Enterprise  

---

## 1. YÊU CẦU HỆ THỐNG (SYSTEM PREREQUISITES)

### Yêu cầu phần cứng tối thiểu:
- **CPU:** 2 Cores (khuyến nghị 4 Cores cho môi trường chịu tải).
- **RAM:** Tối thiểu 4GB RAM (khuyến nghị 8GB RAM).
- **Ổ cứng:** 20GB SSD trống.
- **Hệ điều hành:** Linux (Ubuntu 22.04 LTS / Debian 12 / Rocky Linux 9) hoặc Windows Server 2022 / Windows 10/11 64-bit.

### Yêu cầu phần mềm cài đặt:
- **Cách 1 (Dockerized - Khuyến nghị):** Docker Engine 24.0+ & Docker Compose v2.20+.
- **Cách 2 (Native):**
  - Python 3.12+ (kèm `pip`, `venv`).
  - MySQL Server 8.0+ (hoặc MariaDB 10.11+).
  - Node.js & Ganache CLI (nếu chạy Blockchain thử nghiệm cục bộ).

---

## 2. PHƯƠNG ÁN 1: TRIỂN KHAI NHANH BẰNG DOCKER COMPOSE (KHUYẾN NGHỊ)

Phương án này đóng gói toàn bộ ứng dụng và cơ sở dữ liệu MySQL 8.0 vào container độc lập, đảm bảo môi trường giống nhau 100% trên mọi máy chủ.

### Bước 1: Sao chép tệp cấu hình môi trường
```bash
cp .env.example .env
```
Mở tệp `.env` và cập nhật mật khẩu an toàn cho MySQL và Django:
```ini
DJANGO_SECRET_KEY=khoa_bao_mat_ngau_nhien_dai_hon_50_ky_tu_rat_an_toan_1234567890
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,yourdomain.com
DB_PASSWORD=mat_khau_mysql_phuc_tap_2026
```

### Bước 2: Khởi động hệ thống với Docker Compose
```bash
docker compose up -d --build
```
> **Cơ chế tự động:** Container `web` sẽ tự động chờ container `db` khởi động hoàn tất (qua healthcheck), tự động chạy migrate cơ sở dữ liệu và lệnh `collectstatic`, sau đó kích hoạt Gunicorn WSGI 3 workers.

### Bước 3: Tạo tài khoản Quản trị tối cao (Superuser)
```bash
docker compose exec web python manage.py createsuperuser
```

### Bước 4: Kiểm tra trạng thái và nhật ký hoạt động
```bash
# Xem trạng thái các container
docker compose ps

# Xem log trực tiếp của web service
docker compose logs -f web
```
Truy cập hệ thống tại địa chỉ: `http://localhost:8000/`.

---

## 3. PHƯƠNG ÁN 2: TRIỂN KHAI TRỰC TIẾP TRÊN MÁY CHỦ (NATIVE DEPLOYMENT)

Áp dụng cho môi trường chạy trực tiếp trên Windows hoặc máy chủ Linux không dùng Docker.

### Bước 1: Thiết lập cơ sở dữ liệu MySQL 8.0
Đăng nhập vào MySQL Console:
```sql
CREATE DATABASE english_center_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'english_user'@'localhost' IDENTIFIED BY 'english_secure_password_2026';
GRANT ALL PRIVILEGES ON english_center_db.* TO 'english_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Bước 2: Thiết lập môi trường Python ảo và cài đặt thư viện
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Hoặc trên Linux:
# source .venv/bin/activate

# Cài đặt toàn bộ thư viện dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Đồng bộ dữ liệu và thu thập Static Files
```bash
# Áp dụng tất cả các migration vào MySQL
python manage.py migrate

# Thu thập tệp tĩnh CSS, JS, Fonts
python manage.py collectstatic --noinput

# Tạo tài khoản Quản trị
python manage.py createsuperuser
```

### Bước 4: Khởi chạy Production Server
- **Trên Linux (Gunicorn qua Systemd):**
  ```bash
  gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
  ```
- **Trên Windows (Waitress):**
  ```bash
  pip install waitress
  waitress-serve --port=8000 config.wsgi:application
  ```

---

## 4. CHIẾN LƯỢC SAO LƯU & PHỤC HỒI DỮ LIỆU (BACKUP & RESTORE)

### 1. Lệnh Sao lưu Cơ sở dữ liệu (Backup)
```bash
# Sao lưu nén trực tiếp bằng mysqldump (khuyến nghị chạy hàng ngày lúc 01:00 AM)
mysqldump -u english_user -p --single-transaction --quick --default-character-set=utf8mb4 english_center_db > backup_english_center_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Lệnh Phục hồi Dữ liệu khi gặp sự cố (Restore)
```bash
mysql -u english_user -p --default-character-set=utf8mb4 english_center_db < backup_english_center_20261027.sql
```

---

## 5. BẢNG KIỂM TRA BẢO MẬT TRƯỚC KHI BÀN GIAO (SECURITY CHECKLIST)

Trước khi đưa vào vận hành thực tế tại trung tâm, bắt buộc thực hiện kiểm tra:

| STT | Hạng mục kiểm tra | Trạng thái đạt chuẩn | Cách xác thực |
| :---: | :--- | :---: | :--- |
| 1 | **Chế độ Debug** | `DEBUG = False` | Đảm bảo không lộ stack trace lỗi ra giao diện |
| 2 | **Khóa bí mật** | `SECRET_KEY` mạnh | Dài trên 50 ký tự, sinh ngẫu nhiên |
| 3 | **Deploy Check** | 0 Lỗi | Chạy: `python manage.py check --deploy` |
| 4 | **Cookie An toàn** | `HttpOnly`, `SameSite=Lax` | Ngăn chặn đánh cắp Session qua XSS |
| 5 | **Phòng chống Clickjacking** | `X_FRAME_OPTIONS = "DENY"` | Ngăn chặn nhúng iFrame giả mạo |
| 6 | **Giới hạn Host** | `ALLOWED_HOSTS` chỉ định rõ | Chỉ cho phép domain hoặc IP trung tâm |
| 7 | **Tường lửa MySQL** | Cổng 3306 đóng | Không mở port 3306 ra ngoài Internet |
