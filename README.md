# 🛡️ SafeQR-Cloud (VietQR Threat Intelligence & Intervention Hub)

> **Đề tài:** Nghiên cứu mô hình học máy phát hiện gian lận và đánh giá rủi ro giao dịch VietQR dựa trên phân tích ngữ nghĩa EMVCo  
> **Môn học:** Điện toán đám mây (Cloud Computing) — **Nhóm 19**  
> **Repository:** [https://github.com/sonle-dev/SafeQR-Cloud](https://github.com/sonle-dev/SafeQR-Cloud)

---

## 📌 1. Giới thiệu tổng quan

Trong bối cảnh thanh toán không tiền mặt bùng nổ tại Việt Nam, mã **VietQR** (chuẩn liên ngân hàng NAPAS / EMVCo) trở thành phương thức chuyển khoản phổ biến nhất. Tuy nhiên, các ứng dụng ngân hàng hiện nay chỉ đọc chuỗi QR rồi tự động điền dữ liệu thụ động, không phân tích tính chất thao túng tâm lý (Social Engineering) trong nội dung chuyển tiền. 

Kẻ lừa đảo thường mạo danh cơ quan nhà nước (công an, phạt nguội, VNeID, án phí) để ép buộc người dân (đặc biệt là người cao tuổi) chuyển tiền vào tài khoản cá nhân.

**SafeQR-Cloud** được xây dựng như một **bức tường lửa phân tán (Pre-transaction Threat Intelligence & Intervention Hub)**:
1. **Giải mã cấu trúc TLV** theo quy chuẩn quốc tế **EMVCo Merchant-Presented Mode**.
2. **Kiểm tra tính toàn vẹn** với thuật toán checksum **CRC-16/CCITT-FALSE**.
3. **Phân tích ngữ nghĩa & AI (NLP)**: Phát hiện dấu hiệu ép buộc tâm lý và đối soát mâu thuẫn chéo giữa mục đích công quyền và tài khoản thụ hưởng cá nhân.
4. **Chấm điểm rủi ro $R \in [0, 100]$ & Can thiệp tự động**: Khóa nút chuyển tiền và gửi cảnh báo khẩn cấp qua Telegram Bot đến người thân/người giám hộ khi phát hiện nguy cơ cao.

---

## 🏗️ 2. Kiến trúc Điện toán đám mây (Cloud Architecture)

Hệ thống áp dụng mô hình **Micro-Cloud / Serverless Decoupled Architecture** trên nền tảng Cloud miễn phí (Free Tier) với chi phí 0 VNĐ:

```
[Khách hàng / Người cao tuổi]
              │
              ▼ (1. HTTPS / Global CDN)
     ┌──────────────────┐
     │   Vercel Edge    │  ──► Frontend Web UI (Nút to, chữ lớn, nén ảnh phía client)
     └────────┬─────────┘
              │ (2. Gửi chuỗi QR / ảnh)
              ▼
     ┌──────────────────┐
     │  Render Service  │  ──► Backend FastAPI Core API
     └────────┬─────────┘      • Bộ giải mã EMVCo TLV & Kiểm tra CRC-16
              │                • Động cơ suy luận Học máy (Model ML .pkl)
              │
     ┌────────┴─────────────────────────────────────────┐
     │                                                  │
     ▼ (3. Tra cứu cache & velocity < 10ms)             ▼ (4. Quản lý Blacklist & Log)
┌──────────────────────┐                       ┌──────────────────────┐
│  Upstash Redis Cloud │                       │  Neon Serverless DB  │
│  (In-Memory Cache)   │                       │  (PostgreSQL Cloud)  │
├──────────────────────┤                       ├──────────────────────┤
│ • Cache băm SHA-256  │                       │ • Danh sách đen STK  │
│ • Đếm tần suất quét  │                       │ • Lịch sử cảnh báo   │
│ • Distributed Lock   │                       │ • Thông tin người thân│
└──────────────────────┘                       └──────────────────────┘
     │
     ▼ (5. Kích hoạt khi R >= 70)
┌──────────────────────────────────────┐
│  Telegram Emergency Alert Webhook    │ ──────► [Điện thoại Người bảo hộ / Con cái]
└──────────────────────────────────────┘
```

---

## 📂 3. Cấu trúc thư mục dự án

```text
SafeQR-Cloud/
├── backend/                  # Mã nguồn Backend Core API (FastAPI)
│   ├── app/
│   │   ├── api/              # API router (scan, verify, blacklist, metrics)
│   │   ├── core/             # Cấu hình môi trường, bảo mật, thuật toán CRC-16
│   │   ├── models/           # Pydantic Schemas & DB models
│   │   └── services/         # EMVCo Parser, ML Inference, Redis Cache, Telegram Bot
│   ├── Dockerfile            # Container configuration triển khai Render
│   ├── requirements.txt      # Thư viện phụ thuộc Python
│   └── .env.example          # Mẫu biến môi trường
├── frontend/                 # Giao diện Web tối ưu người cao tuổi (HTML5/Tailwind/JS)
│   ├── index.html            # Giao diện máy quét trực tiếp & kết quả 3 trạng thái
│   ├── js/                   # Xử lý quét camera, giải mã QR và gọi API
│   └── css/                  # Styling độ tương phản cao, nút bấm lớn
├── ml_engine/                # Pipeline Học máy & Xử lý ngôn ngữ tự nhiên
│   ├── data/                 # Tập dữ liệu huấn luyện (dataset.csv)
│   ├── scripts/              # Mã nguồn tiền xử lý tiếng Việt & train mô hình
│   └── models/               # Tệp mô hình đóng gói (vietqr_nlp_model.pkl)
├── database/                 # Script tạo lập và di chuyển cơ sở dữ liệu
│   └── schema.sql            # Cấu trúc bảng PostgreSQL (Neon)
├── docs/                     # Tài liệu nghiên cứu, thiết kế chi tiết & báo cáo
│   └── SPECIFICATION.md      # Đặc tả kỹ thuật toàn diện dự án
├── .gitignore
└── README.md
```

---

## 🧮 4. Động cơ chấm điểm rủi ro (Risk Engine)

Điểm rủi ro tổng hợp $R \in [0, 100]$:

$$R = \min\left(100, \; w_1 \cdot S_{\text{conflict}} + w_2 \cdot (P_{\text{ML}} \times 100) + w_3 \cdot S_{\text{velocity}} + B_{\text{blacklist}}\right)$$

* **$S_{\text{conflict}} \in \{0, 100\}$**: Mâu thuẫn logic giữa mục đích công quyền và tài khoản thụ hưởng cá nhân ($w_1 = 0.40$).
* **$P_{\text{ML}} \in [0, 1]$**: Xác suất văn bản nội dung chuyển tiền mang yếu tố lừa đảo/thao túng ($w_2 = 0.35$).
* **$S_{\text{velocity}} \in [0, 100]$**: Điểm bất thường tần suất quét tài khoản trong 1 giờ qua Redis ($w_3 = 0.25$).
* **$B_{\text{blacklist}}$**: Điểm phạt tuyệt đối ($100$) nếu tài khoản nằm trong danh sách đen đã xác thực.

### Phân cấp ngưỡng can thiệp:
* **$0 \le R < 35$ (AN TOÀN - Xanh lá):** Cho phép sao chép thông tin để chuyển khoản.
* **$35 \le R < 70$ (CẢNH BÁO - Vàng cam):** Cảnh báo tài khoản cá nhân, khuyến cáo gọi điện xác thực.
* **$70 \le R \le 100$ (NGUY HIỂM - Đỏ rực):** **Khóa nút chuyển tiền**, còi cảnh báo kêu, tự động gửi Webhook Telegram đến người thân.

---

## 👥 5. Thành viên nhóm thực hiện (Nhóm 19)

| STT | Họ và tên | Vai trò | Phụ trách chính |
| :---: | :--- | :--- | :--- |
| 1 | **Lê Hồng Sơn** (Trưởng nhóm) | Backend Architecture & EMVCo Engine | Kiến trúc hệ thống, EMVCo TLV Parser, CRC-16, FastAPI, Động cơ tính điểm $R$. |
| 2 | **Lưu Thị Khánh Ly** | AI/NLP Engineer & Data Specialist | Thu thập dataset, Pipeline tiền xử lý tiếng Việt, huấn luyện mô hình ML (`.pkl`). |
| 3 | **Nguyễn Thanh Tùng** | Frontend Developer & UI/UX | Giao diện Web tối ưu người cao tuổi, tích hợp camera quét QR, hiển thị 3 trạng thái. |
| 4 | **Ngô Thị Sinh** | Cloud Architect, QA & Documentation | Cấu hình Cloud (Render, Vercel, Neon, Upstash), Telegram Webhook, Báo cáo & Slide. |

---

## 🚀 6. Hướng dẫn chạy thử nghiệm cục bộ (Local Development)

### Yêu cầu tiên quyết
* Python 3.10+
* Git

### Khởi chạy Backend FastAPI
```bash
# Di chuyển vào thư mục backend
cd backend

# Tạo và kích hoạt môi trường ảo
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt

# Cấu hình biến môi trường
cp .env.example .env

# Chạy server phát triển
uvicorn app.main:app --reload --port 8000
```
Truy cập tài liệu Swagger UI tự động tại: `http://localhost:8000/docs`

---

## 📄 Bản quyền & Giấy phép
Dự án được thực hiện phục vụ mục đích nghiên cứu học tập trong khuôn khổ môn học Điện toán đám mây.
