# 🚀 HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG TRÊN AWS IAAS (EC2 + DOCKER COMPOSE)

Tài liệu này hướng dẫn chi tiết từng bước thiết lập máy chủ ảo **AWS EC2 (IaaS)** để vận hành toàn bộ hệ thống **SafeQR-Cloud** phục vụ báo cáo môn học **Điện toán đám mây (Cloud Computing)**.

---

## 📌 1. Tổng quan Kiến trúc IaaS trên AWS

* **Dịch vụ máy tính (Compute IaaS):** AWS EC2 Instance (Ubuntu 22.04 LTS hoặc 24.04 LTS, dòng `t2.micro` / `t3.micro` thuộc gói AWS Free Tier).
* **Mạng & Bảo mật (Networking & Security):** 
  * AWS VPC & Subnet.
  * AWS Security Groups (Tường lửa ảo): Mở Port 22 (SSH), Port 80 (HTTP), Port 443 (HTTPS); cách ly hoàn toàn Port 5432 (Postgres) và 6379 (Redis) trong mạng nội bộ.
* **Lưu trữ khối (Storage IaaS):** AWS EBS (Elastic Block Store) 20-30 GB General Purpose SSD (gp3).
* **Điều phối Container:** Docker Engine & Docker Compose tự động chạy 4 container:
  1. `safeqr_nginx`: Reverse Proxy & Web Server serving Frontend (Port 80/443).
  2. `safeqr_backend`: FastAPI Core Engine (EMVCo Parser, ML Inference, Risk Engine).
  3. `safeqr_redis`: In-Memory Caching & Bộ đếm tần suất quét (Velocity Counter).
  4. `safeqr_postgres`: Cơ sở dữ liệu quan hệ lưu Blacklist và Scan Logs (Mount vào EBS).

---

## 🛠️ 2. Các bước khởi tạo trên AWS Console (Dành cho chụp ảnh báo cáo)

### Bước 2.1: Khởi tạo EC2 Instance
1. Đăng nhập vào [AWS Management Console](https://aws.amazon.com/console/).
2. Chọn Region gần nhất: **Singapore (`ap-southeast-1`)**.
3. Vào dịch vụ **EC2** ➔ Chọn **Launch Instance**:
   * **Name:** `SafeQR-Cloud-IaaS-Server`
   * **AMI:** `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` (Free Tier eligible).
   * **Instance Type:** `t2.micro` hoặc `t3.micro` (1 vCPU, 1 GB RAM - Free Tier).
   * **Key Pair:** Tạo mới hoặc chọn Key Pair sẵn có (vd: `safeqr-key.pem`) để đăng nhập SSH.

### Bước 2.2: Cấu hình AWS Security Group (Tường lửa)
Tại mục **Network settings**, cấu hình **Inbound Security Group Rules**:

| Type | Protocol | Port Range | Source | Mục đích nghiệp vụ |
| :---: | :---: | :---: | :---: | :--- |
| **SSH** | TCP | `22` | `My IP` | Quản trị máy chủ qua Terminal an toàn |
| **HTTP** | TCP | `80` | `0.0.0.0/0` | Người dùng quét mã và gọi API |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` | Mã hóa SSL/TLS |

*(Lưu ý: Không mở cổng 5432 và 6379 ra ngoài Internet, đảm bảo an toàn thông tin theo chuẩn Cloud Security).*

### Bước 2.3: Gán Elastic IP (IP Tĩnh công khai)
1. Trong menu EC2 bên trái ➔ Chọn **Elastic IPs**.
2. Bấm **Allocate Elastic IP address** ➔ **Associate** vào Instance vừa tạo.
3. Khi đó máy ảo sẽ có một địa chỉ IP cố định (vd: `54.255.xxx.xxx`).

---

## 💻 3. Cấu hình máy chủ ảo qua SSH

### Bước 3.1: Kết nối SSH vào EC2
Mở Terminal trên máy tính và chạy:
```bash
chmod 400 safeqr-key.pem
ssh -i "safeqr-key.pem" ubuntu@<PUBLIC_IP_EC2>
```

### Bước 3.2: Cài đặt Docker & Docker Compose
Chạy chuỗi lệnh sau trên Ubuntu:
```bash
# Cập nhật hệ điều hành
sudo apt update && sudo apt upgrade -y

# Cài đặt Docker
sudo apt install -y docker.io docker-compose-plugin git curl

# Thêm quyền cho user ubuntu không cần gõ sudo
sudo usermod -aG docker ubuntu
newgrp docker

# Kiểm tra phiên bản
docker --version
docker compose version
```

### Bước 3.3: Clone mã nguồn từ GitHub
```bash
git clone https://github.com/sonle-dev/SafeQR-Cloud.git
cd SafeQR-Cloud
```

### Bước 3.4: Khởi chạy toàn bộ hệ thống bằng 1 lệnh duy nhất
```bash
docker compose up -d --build
```

Kiểm tra trạng thái các container:
```bash
docker compose ps
```
Kết quả mong muốn:
```text
NAME                IMAGE               COMMAND                  SERVICE             STATUS              PORTS
safeqr_backend      safeqr-backend      "sh -c 'uvicorn app.…"   backend             running             8000/tcp
safeqr_nginx        nginx:alpine        "/docker-entrypoint.…"   nginx               running             0.0.0.0:80->80/tcp
safeqr_postgres     postgres:16-alpine  "docker-entrypoint.s…"   postgres            running             5432/tcp
safeqr_redis        redis:7-alpine      "docker-entrypoint.s…"   redis               running             6379/tcp
```

---

## 🌐 4. Kiểm thử hệ thống

* **Truy cập Giao diện Web:** Mở trình duyệt và gõ `http://<PUBLIC_IP_EC2>`
* **Truy cập Swagger API Docs:** `http://<PUBLIC_IP_EC2>/docs`
* **Kiểm tra Log thời gian thực:**
  ```bash
  docker compose logs -f backend
  ```
* Khi quét mã lừa đảo trên giao diện Web, hệ thống sẽ:
  1. Khóa nút chuyển tiền trên Web.
  2. Container `safeqr_backend` xử lý bóc tách EMVCo TLV và mô hình NLP.
  3. Bắn tin nhắn khẩn cấp tới **Telegram Bot** trên điện thoại ngay lập tức!
