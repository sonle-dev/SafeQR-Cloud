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
