-- ====================================================================
-- SafeQR-Cloud Database Schema (PostgreSQL - Neon Serverless)
-- ====================================================================

-- 1. Bảng danh sách đen các tài khoản ngân hàng lừa đảo (Blacklist)
CREATE TABLE IF NOT EXISTS blacklists (
    id SERIAL PRIMARY KEY,
    bank_bin VARCHAR(20) NOT NULL,              -- Mã định danh ngân hàng (BIN, vd: 970422 - MBBank)
    account_number VARCHAR(50) NOT NULL,        -- Số tài khoản thụ hưởng
    account_name VARCHAR(255),                  -- Tên chủ tài khoản (nếu có)
    reason TEXT NOT NULL,                       -- Lý do tố giác (Mạo danh công an, lừa đảo việc làm,...)
    evidence_url TEXT,                          -- Đường link chứng cứ/ảnh chụp tố giác
    reported_count INT DEFAULT 1,               -- Số lần bị tố cáo
    status VARCHAR(20) DEFAULT 'VERIFIED',      -- PENDING, VERIFIED, REJECTED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bank_bin, account_number)
);

-- Index tra cứu siêu tốc cho Tag 38
CREATE INDEX IF NOT EXISTS idx_blacklist_lookup ON blacklists (bank_bin, account_number);

-- 2. Bảng cấu hình người giám hộ / con cái nhận cảnh báo khẩn cấp (Guardians)
CREATE TABLE IF NOT EXISTS guardians (
    id SERIAL PRIMARY KEY,
    elder_phone VARCHAR(20) NOT NULL,           -- Số điện thoại người cao tuổi (người dùng quét)
    elder_name VARCHAR(100) NOT NULL,           -- Tên người cao tuổi (vd: Bố Nguyễn Văn A)
    guardian_name VARCHAR(100) NOT NULL,        -- Tên người giám hộ / con cái
    guardian_telegram_chat_id VARCHAR(50) NOT NULL, -- Chat ID Telegram nhận Webhook
    guardian_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (elder_phone, guardian_telegram_chat_id)
);

-- 3. Bảng ghi nhận lịch sử quét và phát hiện rủi ro (Scan Logs)
CREATE TABLE IF NOT EXISTS scan_logs (
    id SERIAL PRIMARY KEY,
    qr_hash VARCHAR(64) NOT NULL,               -- SHA-256 hash của chuỗi raw VietQR
    bank_bin VARCHAR(20),                       -- BIN ngân hàng
    account_number VARCHAR(50),                 -- STK nhận
    amount NUMERIC(15, 2),                      -- Số tiền giao dịch
    message TEXT,                               -- Nội dung lời nhắn chuyển tiền (Tag 62)
    risk_score INT NOT NULL,                    -- Điểm rủi ro tổng hợp R (0 - 100)
    risk_level VARCHAR(20) NOT NULL,            -- SAFE, SUSPICIOUS, HIGH_RISK
    conflict_detected BOOLEAN DEFAULT FALSE,    -- Có mâu thuẫn công quyền vs cá nhân không
    ml_probability FLOAT,                       -- Xác suất ML phát hiện lừa đảo (0.0 - 1.0)
    velocity_count INT DEFAULT 1,               -- Số lần quét tài khoản này trong 1 giờ
    alert_sent BOOLEAN DEFAULT FALSE,           -- Đã bắn cảnh báo Telegram chưa
    client_ip VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index phục vụ thống kê & tra cứu log
CREATE INDEX IF NOT EXISTS idx_scan_logs_qr_hash ON scan_logs (qr_hash);
CREATE INDEX IF NOT EXISTS idx_scan_logs_created_at ON scan_logs (created_at DESC);
