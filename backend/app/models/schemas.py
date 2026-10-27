from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ScanQRRequest(BaseModel):
    raw_qr: str = Field(..., description="Chuỗi ký tự EMVCo thô từ mã VietQR")
    elder_phone: Optional[str] = Field(None, description="Số điện thoại người quét (nếu có)")
    client_ip: Optional[str] = Field(None, description="Địa chỉ IP client")

class BankBeneficiaryInfo(BaseModel):
    bank_bin: str
    account_number: str
    amount: Optional[float] = None
    message: str
    is_valid_crc: bool

class RiskAssessment(BaseModel):
    score: int
    level: str  # SAFE, SUSPICIOUS, HIGH_RISK
    action: str # ALLOW, WARNING, BLOCK_TRANSACTION
    reason: str
    details: Dict[str, Any]

class ScanQRResponse(BaseModel):
    success: bool
    cached: bool = False
    qr_hash: str
    beneficiary: BankBeneficiaryInfo
    risk: RiskAssessment
    alert_triggered: bool = False
    conflict_detected: bool = False
    detected_keywords: List[str] = []

class RegisterGuardianRequest(BaseModel):
    elder_phone: str = Field(..., description="Số điện thoại của người cao tuổi / phụ huynh")
    elder_name: str = Field(..., description="Tên của người cao tuổi (ví dụ: Bố An)")
    guardian_name: str = Field(..., description="Tên của người bảo hộ / con cái (ví dụ: Sơn)")
    guardian_telegram_chat_id: str = Field(..., description="Telegram Chat ID của người bảo hộ")
    guardian_phone: Optional[str] = Field(None, description="Số điện thoại của con cái")

class RegisterGuardianResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class TestAlertRequest(BaseModel):
    scenario: Optional[str] = Field("phat_nguoi", description="Kịch bản mẫu: phat_nguoi, cong_an, khoan_vay, custom")
    bank_name: Optional[str] = Field("MBBank", description="Tên ngân hàng")
    account_number: Optional[str] = Field("0345678901", description="Số tài khoản")
    amount: Optional[float] = Field(3500000.0, description="Số tiền")
    message: Optional[str] = Field("NOP PHAT NGUOI VNEID GIAO THONG", description="Nội dung chuyển tiền")
    risk_score: Optional[int] = Field(95, description="Điểm rủi ro")
    reason: Optional[str] = Field("Mạo danh cơ quan nhà nước yêu cầu nộp phạt vào STK cá nhân", description="Lý do cảnh báo")
    target_chat_id: Optional[str] = Field(None, description="Telegram Chat ID nhận tin (nếu để trống dùng mặc định)")
