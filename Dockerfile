# Sử dụng Python 3.12 slim chính thức từ Docker Hub
FROM python:3.12-slim

# Thiết lập biến môi trường tối ưu cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho mysqlclient và cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Sao chép và cài đặt các dependencies Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn dự án vào container
COPY . /app/

# Tạo thư mục cho staticfiles và media
RUN mkdir -p /app/staticfiles /app/media

# Expose cổng 8000 cho Django Web
EXPOSE 8000

# Lệnh mặc định khởi động ứng dụng bằng Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
