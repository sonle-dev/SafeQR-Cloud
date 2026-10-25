# TÀI LIỆU ĐẶC TẢ VÀ THIẾT KẾ DỰ ÁN NGHIÊN CỨU HỆ THỐNG
**Tên đề tài:** Nghiên cứu mô hình học máy phát hiện gian lận và đánh giá rủi ro giao dịch VietQR dựa trên phân tích ngữ nghĩa EMVCo  
**Tên định danh ứng dụng (Codename):** SafeQR-Cloud (VietQR Threat Intelligence & Intervention Hub)  
**Nhóm thực hiện:** Nhóm 19 (Môn học: Điện toán đám mây - Cloud Computing)  

---

## MỤC LỤC
1. [Tổng quan dự án & Bối cảnh thực tiễn](#1-tổng-quan-dự-án--bối-cảnh-thực-tiễn)
2. [Cơ sở kỹ thuật: Chuẩn mã thanh toán EMVCo / VietQR](#2-cơ-sở-kỹ-thuật-chuẩn-mã-thanh-toán-emvco--vietqr)
3. [Bản chất của "Phân tích ngữ nghĩa" (Semantic Analysis)](#3-bản-chất-của-phân-tích-ngữ-nghĩa-semantic-analysis)
4. [Mô hình Học máy & Động cơ chấm điểm rủi ro](#4-mô-hình-học-máy--động-cơ-chấm-điểm-rủi-ro)
5. [Kiến trúc Điện toán đám mây (Cloud Architecture)](#5-kiến-trúc-điện-toán-đám-mây-cloud-architecture)
6. [Đặc tả Luồng dữ liệu (Input - Processing - Output)](#6-đặc-tả-luồng-dữ-liệu-input---processing---output)
7. [Kế hoạch thực hiện & Phân công công việc (Nhóm 4 người)](#7-kế-hoạch-thực-hiện--phân-công-công-việc-nhóm-4-người)
8. [Kịch bản Thuyết trình & Trình diễn Demo](#8-kịch-bản-thuyết-trình--trình-diễn-demo)
9. [Kết luận và Hướng phát triển](#9-kết-luận-và-hướng-phát-triển)

---

## 1. TỔNG QUAN DỰ ÁN & BỐI CẢNH THỰC TIỄN

### 1.1. Thực trạng nhức nhối tại Việt Nam
Tại Việt Nam, thanh toán không tiền mặt bùng nổ mạnh mẽ với phương thức chuyển khoản qua mã **VietQR** (chuẩn liên ngân hàng do Napas và các ngân hàng thương mại phát triển). Tính năng tự động điền số tài khoản, số tiền và nội dung giúp việc thanh toán trở nên nhanh chóng chỉ với một lần quét camera.

Tuy nhiên, tính năng này đang bị các đối tượng lừa đảo lợi dụng triệt để thông qua các thủ đoạn:
* **Mạo danh cơ quan nhà nước / Công an / Tòa án**: Gửi giấy phạt nguội giao thông giả, trát đòi nợ hoặc văn bản triệu tập có in sẵn mã QR chuyển tiền vào "tài khoản tạm giữ điều tra".
* **Mạo danh Cổng dịch vụ công / Ứng dụng VNeID**: Lừa người dân quét mã QR để "kích hoạt định danh mức 2", "hoàn tất thủ tục bảo hiểm xã hội".
* **Bẫy tuyển dụng / Nhiệm vụ online / Giải ngân khoản vay**: Ép người dùng chuyển tiền "phí bảo hiểm khoản vay" hoặc "phí hoàn tất nhiệm vụ".

### 1.2. Nút thắt của các giải pháp hiện tại
* **Quét mã thụ động**: Các ứng dụng ngân hàng hiện nay chỉ đọc chuỗi QR rồi điền tự động vào ô chuyển tiền; ứng dụng không kiểm tra xem nội dung chuyển tiền có mang tính chất thao túng tâm lý (Social Engineering) hay không.
* **Đối tượng dễ bị tổn thương**: Người cao tuổi, người ít hiểu biết về công nghệ thường hoảng sợ khi đọc các từ ngữ đe dọa và bấm chuyển tiền ngay trên app ngân hàng mà không nhận ra tài khoản nhận tiền là tài khoản cá nhân thông thường.

### 1.3. Mục tiêu của dự án SafeQR-Cloud
Xây dựng một nền tảng Cloud phân tán đóng vai trò như một **tấm khiên trung gian (Tường lửa phân tích trước giao dịch)**:
1. Giải mã trực tiếp cấu trúc mã VietQR theo chuẩn quốc tế EMVCo.
2. Ứng dụng mô hình **Học máy & Xử lý ngôn ngữ tự nhiên (NLP)** để phát hiện hành vi thao túng tâm lý cài cắm trong nội dung chuyển tiền.
3. Nhận diện sự mâu thuẫn ngữ nghĩa giữa mục đích giao dịch và loại hình tài khoản thụ hưởng.
4. Ngăn chặn chuyển khoản và lập tức gửi cảnh báo khẩn cấp (qua Webhook Telegram/Zalo) tới người thân/người giám hộ khi phát hiện nguy cơ cao.

---

## 2. CƠ SỞ KỸ THUẬT: CHUẨN MÃ THANH TOÁN EMVCO / VIETQR

Mã VietQR bản chất không phải là một đường link web hay một tệp nhị phân phức tạp, mà là một **chuỗi ký tự văn bản thuần túy (Plain Text)** tuân theo quy chuẩn **EMVCo Merchant-Presented Mode**.

Chuỗi dữ liệu được tổ chức theo cấu trúc lồng nhau dạng **TLV (Tag - Length - Value)**:
* **Tag (Mã thẻ)**: 2 ký tự số định danh loại thông tin.
* **Length (Độ dài)**: 2 ký tự số xác định số ký tự của trường Value.
* **Value (Giá trị)**: Dữ liệu thực tế.

### Bảng đặc tả các trường dữ liệu cốt lõi trong VietQR

| Tag | Định danh trường | Ý nghĩa nghiệp vụ | Ví dụ chuỗi con |
| :---: | :--- | :--- | :--- |
| **`00`** | Payload Format Indicator | Phiên bản chuẩn dữ liệu (cố định là `01`) | `000201` |
| **`01`** | Point of Initiation Method | `11`: QR động (có số tiền); `12`: QR tĩnh | `010212` |
| **`38`** | Merchant Account Information | Khối thông tin định danh thụ hưởng (NAPAS + BIN Ngân hàng + STK) | `3854...` |
| **`53`** | Transaction Currency | Đơn vị tiền tệ chuẩn ISO 4217 (`704` là VNĐ) | `5303704` |
| **`54`** | Transaction Amount | Số tiền giao dịch bắt buộc | `54075000000` (5.000.000 đ) |
| **`58`** | Country Code | Mã quốc gia theo chuẩn ISO 3166-1 alpha-2 | `5802VN` |
| **`62`** | Additional Data Field | **Dữ liệu bổ sung: Chứa nội dung/lời nhắn chuyển khoản (Sub-tag 08)** | `62250821NOP PHAT NGUOI VNEID` |
| **`63`** | CRC Checksum | Mã kiểm tra tính toàn vẹn 16-bit (CRC-16/CCITT-FALSE) | `6304ABCD` |

---

## 3. BẢN CHẤT CỦA "PHÂN TÍCH NGỮ NGHĨA" (SEMANTIC ANALYSIS)

Để tránh nhầm lẫn giữa việc bóc tách chuỗi đơn thuần (Syntax Parsing) và phân tích chiều sâu, hệ thống chia việc phân tích thành 3 tầng:

```
                  ┌─────────────────────────────────────────┐
                  │          CHUỖI RAW VIETQR               │
                  └────────────────────┬────────────────────┘
                                       │
                      [Tầng 1: Phân tích cú pháp (Syntax)]
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          Tag 38: BIN & STK                    Tag 62: Lời nhắn chuyển tiền
          (Vd: MBBank - 0345678901)            (Vd: "NOP PHAT NGUOI VNEID")
                     │                                   │
                     └─────────────────┬─────────────────┘
                                       │
                    [Tầng 2: Phân tích ngữ nghĩa (Semantics)]
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
[Ngữ nghĩa Nội dung]         [Đối soát Ngữ nghĩa Chéo]        [Ngữ cảnh Bất thường]
• Ý định: Đòi phạt hành chính • Mâu thuẫn: Cơ quan nhà nước     • Đột biến tần suất quét
• Tâm lý: Ép buộc, dọa nạt     KHÔNG dùng STK cá nhân          • Lịch sử tài khoản nhận tiền
• Ngụy trang: Chống né từ     • Kết luận: Semantic Mismatch
```

1. **Phân tích ngữ nghĩa nội dung (Content Semantic Parsing - Tag 62)**:
   * **Nhận diện ý định (Intent Recognition)**: Hệ thống xác định nội dung thuộc nhóm: Giao dịch thông thường (ăn uống, mua hàng, tiền trọ) hay Mạo danh công quyền (phạt nguội, viện kiểm sát, VNeID, hoàn tất hồ sơ).
   * **Phát hiện dấu hiệu thúc ép tâm lý (Urgency & Threat Detection)**: Nhận diện các cấu trúc câu dồn ép thời gian ("trong 24h", "ngay lập tức") hoặc đe dọa tố tụng ("khởi tố", "lệnh bắt", "phong tỏa tài khoản").
   * **Chuẩn hóa biến thể ngụy trang**: Khôi phục các ký tự bị cố tình chèn dấu chấm, dấu cách (`n.o.p p.h.a.t`, `p h a t n g u o i`) về từ gốc để xử lý.
2. **Đối soát ngữ nghĩa chéo (Cross-Field Semantic Verification)**:
   * **Mâu thuẫn chủ thể (Entity Inconsistency)**: Theo quy định pháp luật Việt Nam, tiền phạt vi phạm hành chính hoặc lệ phí nhà nước **chỉ được nộp vào Kho bạc Nhà nước hoặc tài khoản định danh pháp nhân chuyên thu**, tuyệt đối không nộp vào tài khoản cá nhân tại ngân hàng thương mại. Nếu Tag 62 mang ngữ nghĩa "nộp phạt/án phí" nhưng Tag 38 là tài khoản cá nhân $\rightarrow$ Mâu thuẫn logic $100\%$ lừa đảo.
3. **Phân tích ngữ cảnh tần suất (Temporal Semantic Context)**:
   * Phân tích lịch sử truy vấn của số tài khoản trong bộ đệm thời gian thực (Upstash Redis). Nếu một tài khoản bất ngờ nhận được hàng chục yêu cầu quét trong vài giờ với các nội dung giống nhau $\rightarrow$ Dấu hiệu của một chiến dịch lừa đảo diện rộng.

---

## 4. MÔ HÌNH HỌC MÁY & ĐỘNG CƠ CHẤM ĐIỂM RỦI RO

### 4.1. Pipeline Xử lý Ngôn ngữ Tự nhiên & Học máy (ML/NLP Pipeline)
Mô hình học máy chịu trách nhiệm phân loại chuỗi nội dung văn bản bóc tách từ Sub-tag `08` của Tag `62`.

```
[Text thô từ Tag 62] 
        │
        ▼ 
[Tiền xử lý: Chuyển chữ thường, xóa ký tự đặc biệt, chuẩn hóa Unicode]
        │
        ▼ 
[Tách từ tiếng Việt (Word Segmentation qua Underthesea / PyVi)]
        │
        ▼ 
[Vector hóa đặc trưng (TF-IDF Vectorizer với n-gram 1-3)]
        │
        ▼ 
[Mô hình Phân loại (LinearSVC / MultinomialNB / Logistic Regression)]
        │
        ▼ 
[Xác suất rủi ro thao túng tâm lý: P_ML ∈ [0, 1]]
```

* **Dataset huấn luyện**: Thu thập và xây dựng tập dữ liệu gồm hơn 1.000 mẫu câu nội dung giao dịch tại Việt Nam (Gán nhãn nhị phân: `0 - Bình thường`, `1 - Lừa đảo/Đe dọa`).
* **Lý do chọn ML truyền thống thay vì LLM cồng kềnh**: 
  * Dung lượng mô hình sau khi đóng gói (`.pkl`) chỉ khoảng vài trăm KB đến 2 MB.
  * Tốc độ suy luận (Inference time) cực nhanh ($< 5\text{ms}$), không tốn chi phí GPU.
  * Phù hợp tối đa với tài nguyên giới hạn (RAM 512MB) của gói Cloud PaaS miễn phí (Render).

### 4.2. Công thức toán học chấm điểm rủi ro tổng hợp

Tổng điểm rủi ro $R \in [0, 100]$ được xác định theo mô hình hàm đa trọng số:

$$R = \min\left(100, \; w_1 \cdot S_{\text{conflict}} + w_2 \cdot (P_{\text{ML}} \times 100) + w_3 \cdot S_{\text{velocity}} + B_{\text{blacklist}}\right)$$

Trong đó:
* $S_{\text{conflict}} \in \{0, 100\}$: Điểm mâu thuẫn ngữ nghĩa giữa mục đích thu phạt/công quyền và tài khoản cá nhân ($w_1 = 0.40$).
* $P_{\text{ML}} \in [0, 1]$: Xác suất nội dung mang tính thao túng tâm lý do mô hình Học máy dự đoán ($w_2 = 0.35$).
* $S_{\text{velocity}} \in [0, 100]$: Điểm bất thường về tần suất quét trong 1 giờ qua tính bằng Redis ($w_3 = 0.25$).
* $B_{\text{blacklist}}$: Điểm phạt tuyệt đối. Nếu số tài khoản hoặc chuỗi QR nằm trong danh sách đen tố giác đã được kiểm chứng $\rightarrow B_{\text{blacklist}} = 100$.

### 4.3. Phân cấp ngưỡng can thiệp (Action Thresholds)

| Dải điểm $R$ | Phân loại trạng thái | Giao diện hiển thị | Hành vi hệ thống |
| :---: | :---: | :---: | :--- |
| **$0 \le R < 35$** | **AN TOÀN** (Safe) | Màu Xanh lá | Hiển thị đầy đủ thông tin, cho phép sao chép/mở app chuyển tiền bình thường. |
| **$35 \le R < 70$** | **CẢNH BÁO** (Suspicious) | Màu Vàng cam | Hiển thị khuyến cáo: "Tài khoản cá nhân, hãy gọi điện xác thực lại người nhận trước khi chuyển". |
| **$70 \le R \le 100$** | **NGUY HIỂM** (High Risk) | Màu Đỏ rực | **KHÓA NÚT CHUYỂN TIỀN**, còi cảnh báo kêu, tự động kích hoạt Webhook báo về điện thoại con cái/người bảo hộ. |

---

## 5. KIẾN TRÚC ĐIỆN TOÁN ĐÁM MÂY (CLOUD ARCHITECTURE)

Dự án áp dụng mô hình **Micro-Cloud / Serverless Decoupled Architecture**, phối hợp các nhà cung cấp dịch vụ đám mây chuyên biệt có gói Free Tier:

```
[Khách hàng / Người cao tuổi]
              │
              ▼ (1. Truy cập Web qua HTTPS / CDN)
     ┌──────────────────┐
     │  Vercel Edge     │  (Frontend React/Next.js UI)
     └────────┬─────────┘  • Nút bấm lớn, tối giản cho người già
              │            • Nén ảnh trực tiếp trên trình duyệt
              │
              ▼ (2. Gửi Payload: Ảnh hoặc Chuỗi QR)
     ┌──────────────────┐
     │  Render Service  │  (Backend FastAPI Core API)
     └────────┬─────────┘  • EMVCo TLV Parser
              │            • Inference Engine (Chạy model ML .pkl)
              │
     ┌────────┴─────────────────────────────────────────┐
     │                                                  │
     ▼ (3. Tra cứu siêu tốc < 10ms)                     ▼ (4. Quản lý bản ghi & Báo cáo)
┌──────────────────────┐                       ┌──────────────────────┐
│  Upstash Redis Cloud │                       │  Neon Serverless DB  │
│  (In-Memory Cache)   │                       │  (PostgreSQL Cloud)  │
├──────────────────────┤                       ├──────────────────────┤
│ • Cache kết quả quét │                       │ • Bảng Blacklist     │
│ • Bộ đếm Velocity    │                       │ • Lịch sử cảnh báo   │
│ • Distributed Lock   │                       │ • Quản lý Người thân │
└──────────────────────┘                       └──────────────────────┘
     │
     ▼ (5. Kích hoạt khi R >= 70)
┌──────────────────────────────────────┐
│ Emergency Alert Webhook (Telegram)   │ ──────► [Điện thoại Người thân / Con cái]
└──────────────────────────────────────┘
```

### Đánh giá các dịch vụ Cloud được lựa chọn (Đáp ứng tiêu chí môn học)

| Tên dịch vụ Cloud | Loại dịch vụ | Vai trò trong hệ thống | Lý do lựa chọn & Tính hợp lý |
| :--- | :---: | :--- | :--- |
| **Vercel** | PaaS (Frontend) | Host giao diện người dùng Web | Miễn phí, hỗ trợ tự động build từ GitHub, tích hợp CDN toàn cầu, cấp sẵn SSL/HTTPS. |
| **Render** | PaaS (Compute) | Host Web Service FastAPI & Model ML | Miễn phí không cần add thẻ, hỗ trợ môi trường Python chuẩn, tự động quản trị container. |
| **Upstash** | Serverless In-Memory | Lưu trữ Cache kết quả và quản lý Rate-limit | Gói miễn phí 10.000 requests/ngày không cần thẻ, độ trễ truy vấn cực thấp (< 10ms). |
| **Neon.tech** | Serverless DB | Cơ sở dữ liệu quan hệ PostgreSQL | Tự động co giãn (Auto-scaling), hỗ trợ Branching DB, có giao diện quản trị Web trực quan. |

---

## 6. ĐẶC TẢ LUỒNG DỮ LIỆU (INPUT - PROCESSING - OUTPUT)

### 6.1. Input (Dữ liệu đầu vào)
* **Dữ liệu quét trực tiếp**: Ảnh chụp mã VietQR (từ camera điện thoại/tệp ảnh tải lên) hoặc chuỗi text thô theo chuẩn EMVCo.
* **Dữ liệu cấu hình giám hộ**: Số điện thoại hoặc `Chat_ID` Telegram của người bảo hộ/con cái đã liên kết với tài khoản người già.
* **Dữ liệu báo cáo cộng đồng**: Số tài khoản, ngân hàng thụ hưởng và ảnh chụp chứng cứ lừa đảo do người dùng đóng góp.

### 6.2. Processing (Nội hàm xử lý tuần tự)
1. **Bước 1 (Client-side)**: Giao diện Web tiếp nhận ảnh, sử dụng thư viện xử lý ảnh bóc tách ma trận mã vạch để đọc ra chuỗi ký tự thô EMVCo.
2. **Bước 2 (Cache Lookup)**: Backend băm chuỗi thô bằng thuật toán `SHA-256`, kiểm tra trên Upstash Redis:
   * Nếu có trong Cache (Cache Hit): Trả kết quả phân tích ngay lập tức ($< 10\text{ms}$).
   * Nếu chưa có (Cache Miss): Chuyển tiếp vào pipeline phân tích.
3. **Bước 3 (EMVCo Parsing)**: Thuật toán con trỏ duyệt chuỗi TLV trích xuất các trường: Tag `38` (BIN ngân hàng, STK), Tag `54` (Số tiền), Tag `62` (Sub-tag 08 - Nội dung lời nhắn), Tag `63` (Checksum CRC-16).
4. **Bước 4 (Integrity Check)**: Kiểm tra mã CRC-16; nếu không khớp, từ chối xử lý và báo mã QR bị lỗi/chỉnh sửa.
5. **Bước 5 (ML Semantic Inference)**: Đưa chuỗi nội dung Tag 62 vào mô hình Học máy để trích xuất xác suất rủi ro $P_{\text{ML}}$.
6. **Bước 6 (Risk Calculation)**: Tính tổng điểm rủi ro $R$ theo công thức tổng hợp, ghi nhận lượt quét vào bộ đếm tần suất của Redis.
7. **Bước 7 (Intervention Routing)**:
   * Nếu $R \ge 70$: Ghi log vào Neon PostgreSQL và kích hoạt Webhook bắn thông báo khẩn cấp tới Telegram của con cái.
   * Ghi kết quả vào Redis Cache với thời gian sống (TTL) 3.600 giây (1 giờ).

### 6.3. Output (Kết quả đầu ra)
* **Phía người dùng (Người già)**:
  * Trạng thái cảnh báo trực quan (Xanh / Vàng / Đỏ).
  * Chi tiết đối chiếu: Tên ngân hàng, Số tài khoản, Tên tài khoản, Số tiền, Mục đích phát hiện.
  * Lời khuyên an toàn: Khóa nút chuyển tiền nếu nguy hiểm, hướng dẫn kiểm tra lại với người thân.
* **Phía người bảo hộ (Con cái)**:
  * Tin nhắn báo động thời gian thực trên điện thoại: Tên bố mẹ, số tiền chuẩn bị chuyển, số tài khoản đích và bằng chứng lừa đảo phát hiện được.

---

## 7. KẾ HOẠCH THỰC HIỆN & PHÂN CÔNG CÔNG VIỆC (NHÓM 4 NGƯỜI)

### 7.1. Bảng phân công trách nhiệm chi tiết (RACI Matrix)

| Thành viên | Vai trò chính | Nhiệm vụ chi tiết | Sản phẩm bàn giao cụ thể |
| :--- | :--- | :--- | :--- |
| **Lê Hồng Sơn** (Trưởng nhóm) | Backend Architecture & EMVCo Engine | • Thiết kế kiến trúc hệ thống tổng thể.<br>• Viết module EMVCo TLV Parser & CRC-16 Validator.<br>• Xây dựng Core API bằng Python FastAPI.<br>• Viết hàm tính toán điểm rủi ro tổng hợp $R$. | • Mã nguồn Backend FastAPI hoàn chỉnh.<br>• Tài liệu đặc tả API (Swagger UI). |
| **Lưu Thị Khánh Ly** | AI/NLP Engineer & Data Specialist | • Thu thập và gán nhãn tập dữ liệu nội dung chuyển tiền (Dataset).<br>• Xây dựng Pipeline tiền xử lý tiếng Việt & TF-IDF Vectorizer.<br>• Huấn luyện và đánh giá mô hình học máy (So sánh Naive Bayes, LinearSVC, Logistic Regression).<br>• Đóng gói model ra tệp `.pkl`. | • Tệp dữ liệu huấn luyện `dataset.csv`.<br>• Model đóng gói `vietqr_nlp_model.pkl`.<br>• Báo cáo chỉ số Accuracy, F1-Score, Confusion Matrix. |
| **Nguyễn Thanh Tùng** | Frontend Developer & UI/UX | • Thiết kế giao diện Web tương thích Mobile.<br>• Tối ưu trải nghiệm cho người cao tuổi: Font chữ lớn, tương phản cao, nút bấm to.<br>• Tích hợp camera quét QR trực tiếp và tải tệp ảnh.<br>• Xử lý hiển thị kết quả phân tích trực quan 3 màu (Xanh/Vàng/Đỏ). | • Mã nguồn Frontend (React/Next.js hoặc HTML5/Tailwind/JS).<br>• Giao diện Web mượt mà, phản hồi tốt trên điện thoại. |
| **Ngô Thị Sinh** | Cloud Architect, QA & Documentation | • Khởi tạo và liên kết các tài khoản Cloud (Render, Vercel, Neon, Upstash).<br>• Thiết lập biến môi trường, Dockerfile và pipeline CI/CD.<br>• Cấu hình Bot Telegram và Webhook cảnh báo.<br>• Chịu trách nhiệm chính viết **Báo cáo 20 trang** (chụp ảnh từng bước thao tác Cloud) và dựng Slide thuyết trình. | • Hạ tầng Cloud trực tuyến 100%.<br>• File báo cáo Word/PDF chuẩn mẫu 20 trang.<br>• Kịch bản và Slide thuyết trình. |

### 7.2. Kế hoạch tiến độ 4 tuần

```
Tuần 1: Khảo sát & Thiết kế
├── Nghiên cứu đặc tả chuẩn EMVCo & VietQR
├── Thu thập mẫu nội dung lừa đảo & Khởi tạo CSDL Neon, Redis
└── Hoàn thành Mục 1, Mục 2, Mục 3 Báo cáo

Tuần 2: Lập trình Cốt lõi & Huấn luyện Model
├── Xây dựng module Parser EMVCo & Tính toán Checksum
├── Huấn luyện mô hình NLP phân loại văn bản tiếng Việt
└── Hoàn thành Mục 4 Báo cáo

Tuần 3: Tích hợp Hệ thống & Xây dựng Giao diện
├── Xây dựng Core API (FastAPI) kết nối Model ML và Redis Cache
├── Lập trình giao diện Frontend cho người cao tuổi
└── Kết nối Webhook cảnh báo khẩn cấp qua Telegram

Tuần 4: Triển khai Cloud, Kiểm thử & Đóng gói Báo cáo
├── Deploy Backend lên Render, Frontend lên Vercel
├── Chụp ảnh chi tiết từng bước cấu hình Cloud (Mục 5)
├── Chụp ảnh màn hình các ca kiểm thử thành công (Mục 6)
└── Hoàn thiện Mục 7, in ấn báo cáo 20 trang và tập dượt Demo
```

---

## 8. KỊCH BẢN THUYẾT TRÌNH & TRÌNH DIỄN DEMO

Để đạt điểm tuyệt đối trước hội đồng chấm điểm, nhóm sẽ vận hành kịch bản demo 3 bước rõ ràng trong vòng 5 phút:

### Bước 1: Trình diễn ca giao dịch An toàn (Safe Case)
* **Thao tác**: Người thuyết trình mở ứng dụng trên điện thoại, quét một mã VietQR thanh toán tiền ăn trưa bình thường:
  * STK: `1903...` (Techcombank)
  * Số tiền: `45.000 đ`
  * Nội dung: `com trua van phong`
* **Kết quả**: Hệ thống phản hồi sau 0.2 giây. Màn hình hiện khung **Màu Xanh Lá**: *"Giao dịch bình thường - Xác minh tài khoản cá nhân hợp lệ"*. Cho phép sao chép thông tin để thực hiện chuyển khoản.

### Bước 2: Trình diễn ca lừa đảo Mạo danh Công an / Phạt nguội (Fraud Case)
* **Thao tác**: Người thuyết trình quét mã QR in trên một tờ giấy giả mạo trát phạt nguội:
  * STK: `0345...` (Tài khoản cá nhân)
  * Số tiền: `3.500.000 đ`
  * Nội dung: `NOP PHAT NGUOI VNEID GIAO THONG`
* **Kết quả**: 
  1. Màn hình điện thoại nhấp nháy **Màu Đỏ Rực**, còi cảnh báo vang lên:  
     **"CẢNH BÁO LỪA ĐẢO NGUY HIỂM: PHÁT HIỆN DẤU HIỆU MẠO DANH CÔNG QUYỀN!"**
  2. Bảng phân tích chỉ rõ:
     * *Mâu thuẫn ngữ nghĩa*: Đòi nộp phạt công quyền nhưng thụ hưởng là tài khoản cá nhân.
     * *Học máy phát hiện*: Phát hiện chuỗi từ khóa đe dọa thao túng tâm lý.
     * *Hành vi can thiệp*: **Nút chuyển tiền bị vô hiệu hóa hoàn toàn**.
  3. **Ngay lập tức (sau 1 giây)**: Điện thoại của một thành viên khác trong nhóm đóng vai "Con cái" rung lên nhận tin nhắn từ Telegram Bot:  
     *"Bố/Mẹ bạn vừa quét mã chuyển tiền lừa đảo phạt nguội 3.500.000đ vào STK lạ. Hệ thống đã chặn lại. Hãy gọi ngay cho bố mẹ!"*

### Bước 3: Chứng minh Hạ tầng Điện toán đám mây (Cloud Verification)
* **Thao tác**: Chiếu trực tiếp trình duyệt trên máy tính lên máy chiếu:
  * Mở tab **Render Logs**: Chỉ cho thầy cô thấy log request vừa bay lên container trên Cloud, mô hình ML chạy suy luận và bóc tách chuỗi trong vài mili-giây.
  * Mở tab **Upstash Redis Console**: Cho thấy số lượng key trong cache vừa tăng lên, chứng minh dữ liệu được lưu tạm trên RAM Cloud.
  * Mở tab **Neon PostgreSQL**: Cho thấy bản ghi cảnh báo vừa được insert vào cơ sở dữ liệu trên Cloud theo thời gian thực.

---

## 9. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 9.1. Đóng góp của dự án
* **Về mặt học thuật & công nghệ**: Chứng minh tính khả thi của việc kết hợp giữa phân tích đặc tả thanh toán tài chính (EMVCo) và mô hình Học máy xử lý ngôn ngữ tự nhiên để giải bài toán an toàn thông tin tại Việt Nam.
* **Về mặt kỹ thuật Cloud**: Xây dựng thành công một hệ thống hướng sự kiện (Event-driven), tối ưu hóa bộ đệm phân tán (Distributed Caching) trên các nền tảng Cloud hiện đại với chi phí 0 VNĐ nhưng vẫn đảm bảo hiệu năng và độ ổn định cao.
* **Về mặt giá trị xã hội**: Cung cấp giải pháp bảo vệ chủ động cho người cao tuổi và nhóm người dùng yếu thế, ngăn chặn nguy cơ mất tài sản trước khi giao dịch thực sự diễn ra.

### 9.2. Hướng phát triển tiếp theo
* Phát triển thành **Tiện ích mở rộng (Extension)** trên trình duyệt hoặc tích hợp thành **Bộ thư viện SDK (Mobile SDK)** để các ví điện tử và ứng dụng ngân hàng có thể nhúng trực tiếp vào tính năng quét mã QR sẵn có.
* Mở rộng mô hình học máy: Nâng cấp lên các mô hình ngôn ngữ tiếng Việt chuyên biệt để phát hiện các kịch bản lừa đảo ngày càng tinh vi và phức tạp hơn.