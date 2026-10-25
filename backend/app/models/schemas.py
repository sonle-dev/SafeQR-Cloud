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
