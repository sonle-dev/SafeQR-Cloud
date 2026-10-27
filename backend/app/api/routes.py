import hashlib
from fastapi import APIRouter, HTTPException, status
from ..models.schemas import ScanQRRequest, ScanQRResponse, BankBeneficiaryInfo, RiskAssessment
from ..services.emvco_parser import VietQRData
from ..services.risk_engine import check_semantic_conflict, calculate_risk_score
from ..services.telegram_service import send_scam_alert
from ..services.ml_service import predict_fraud_probability

router = APIRouter(prefix="/api/v1", tags=["VietQR Security Scanner"])

# Popular Vietnamese Bank BIN mapping for reference
VIETNAM_BANKS = {
    "970422": "MBBank (Ngân hàng Quân Đội)",
    "970407": "Techcombank",
    "970436": "Vietcombank",
    "970415": "VietinBank",
    "970418": "BIDV",
    "970405": "Agribank",
    "970423": "TPBank",
    "970432": "VPBank",
    "970403": "Sacombank",
    "970441": "VIB"
}

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "SafeQR-Cloud Core API", "version": "1.0.0"}

@router.get("/banks")
def get_supported_banks():
    return {"status": "success", "data": VIETNAM_BANKS}

@router.post("/scan", response_model=ScanQRResponse)
async def scan_and_evaluate_qr(payload: ScanQRRequest):
    raw_qr = payload.raw_qr.strip()
    if not raw_qr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chuỗi QR không được để trống!"
        )
        
    # 1. Calculate SHA-256 hash of raw QR for cache key
    qr_hash = hashlib.sha256(raw_qr.encode('utf-8')).hexdigest()
    
    # 2. Parse EMVCo TLV structure
    qr_data = VietQRData(raw_qr)
    if not qr_data.is_valid_crc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mã QR không hợp lệ hoặc sai mã toàn vẹn CRC-16 (EMVCo Tag 63)!"
        )
        
    # 3. Check Semantic Conflict (Công quyền vs Tài khoản cá nhân)
    has_conflict, conflict_score, detected_kw = check_semantic_conflict(qr_data.message)
    
    # 4. ML Semantic Inference
    ml_prob = predict_fraud_probability(qr_data.message)
    if has_conflict and ml_prob < 0.5:
        # Boost confidence when cross-field semantic conflict is clearly detected
        ml_prob = max(ml_prob, 0.75)
    
    # 5. Velocity and Blacklist
    velocity_count = 1
    is_blacklisted = False
    
    # 6. Calculate Risk Score R
    risk = calculate_risk_score(
        conflict_score=conflict_score,
        ml_probability=ml_prob,
        velocity_count=velocity_count,
        is_blacklisted=is_blacklisted
    )
    
    alert_triggered = False
    # If high risk (R >= 70), dispatch emergency Telegram alert
    if risk["score"] >= 70:
        bank_name = VIETNAM_BANKS.get(qr_data.bank_bin, f"Mã BIN: {qr_data.bank_bin}")
        alert_sent = await send_scam_alert(
            bank_name=bank_name,
            account_number=qr_data.account_number,
            amount=qr_data.amount,
            message=qr_data.message,
            risk_score=risk["score"],
            risk_reason=risk["reason"]
        )
        alert_triggered = alert_sent
    
    return ScanQRResponse(
        success=True,
        cached=False,
        qr_hash=qr_hash,
        beneficiary=BankBeneficiaryInfo(
            bank_bin=qr_data.bank_bin,
            account_number=qr_data.account_number,
            amount=qr_data.amount,
            message=qr_data.message,
            is_valid_crc=qr_data.is_valid_crc
        ),
        risk=RiskAssessment(
            score=risk["score"],
            level=risk["level"],
            action=risk["action"],
            reason=risk["reason"],
            details=risk["details"]
        ),
        alert_triggered=alert_triggered,
        conflict_detected=has_conflict,
        detected_keywords=detected_kw
    )
