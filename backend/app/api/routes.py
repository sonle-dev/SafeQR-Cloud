import hashlib
from fastapi import APIRouter, HTTPException, status
from ..models.schemas import (
    ScanQRRequest, ScanQRResponse, BankBeneficiaryInfo, RiskAssessment,
    RegisterGuardianRequest, RegisterGuardianResponse, TestAlertRequest
)
from ..services.emvco_parser import VietQRData
from ..services.risk_engine import check_semantic_conflict, calculate_risk_score
from ..services.telegram_service import send_scam_alert
from ..services.ml_service import predict_fraud_probability
from ..services.db_service import register_guardian, get_guardians_for_phone, send_registration_confirmation

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

@router.post("/test/send-alert")
async def api_test_send_alert(payload: TestAlertRequest):
    """
    Endpoint phục vụ thuyết trình & kiểm thử: Bắn trực tiếp cảnh báo về Telegram.
    """
    scenarios = {
        "phat_nguoi": {
            "bank_name": "MBBank (Ngân hàng Quân Đội)",
            "account_number": "0345678901",
            "amount": 3500000.0,
            "message": "NOP PHAT NGUOI VNEID TRONG 24H",
            "risk_score": 95,
            "reason": "Mạo danh Cục CSGT / VNeID yêu cầu nộp phạt vi phạm vào STK cá nhân"
        },
        "cong_an": {
            "bank_name": "Techcombank",
            "account_number": "1903888888",
            "amount": 50000000.0,
            "message": "CHUYEN TIEN TAM GIU DIEU TRA AN MA TUY",
            "risk_score": 100,
            "reason": "Mạo danh Cơ quan Cảnh sát Điều tra / Viện Kiểm sát đe dọa lệnh bắt tạm giam"
        },
        "khoan_vay": {
            "bank_name": "VPBank",
            "account_number": "0987654321",
            "amount": 5000000.0,
            "message": "PHI GIAI NGAN BAO HIEM KHOAN VAY TIN DUNG",
            "risk_score": 85,
            "reason": "Bẫy lừa đảo giải ngân khoản vay online: Ép nộp phí bảo hiểm khoản vay trước"
        }
    }

    if payload.scenario in scenarios:
        sc = scenarios[payload.scenario]
        bank = sc["bank_name"]
        acc = sc["account_number"]
        amt = sc["amount"]
        msg = sc["message"]
        score = sc["risk_score"]
        reason = sc["reason"]
    else:
        bank = payload.bank_name or "MBBank"
        acc = payload.account_number or "0345678901"
        amt = payload.amount or 3500000.0
        msg = payload.message or "NOP PHAT NGUOI GIAO THONG"
        score = payload.risk_score or 95
        reason = payload.reason or "Phát hiện mâu thuẫn ngữ nghĩa và thao túng tâm lý"

    target_chat = payload.target_chat_id or None

    success = await send_scam_alert(
        bank_name=bank,
        account_number=acc,
        amount=amt,
        message=msg,
        risk_score=score,
        risk_reason=reason,
        target_chat_id=target_chat
    )

    if success:
        return {"status": "success", "message": f"Đã gửi cảnh báo [{msg}] tới Telegram thành công!"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gửi tin nhắn Telegram thất bại. Kiểm tra Bot Token hoặc kết nối mạng."
        )
async def api_register_guardian(payload: RegisterGuardianRequest):
    """
    Self-declaration endpoint: Con cái tự khai báo SĐT của bố mẹ và Telegram Chat ID.
    """
    if not payload.elder_phone.strip() or not payload.guardian_telegram_chat_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số điện thoại người thân và Telegram Chat ID không được để trống!"
        )

    record = register_guardian(
        elder_phone=payload.elder_phone,
        elder_name=payload.elder_name,
        guardian_name=payload.guardian_name,
        chat_id=payload.guardian_telegram_chat_id,
        guardian_phone=payload.guardian_phone
    )

    # Send a confirmation alert message to the guardian Telegram
    await send_registration_confirmation(
        chat_id=payload.guardian_telegram_chat_id,
        elder_name=payload.elder_name,
        elder_phone=payload.elder_phone,
        guardian_name=payload.guardian_name
    )

    return RegisterGuardianResponse(
        success=True,
        message=f"Đã liên kết bảo vệ thành công cho {payload.elder_name} ({payload.elder_phone})!",
        data=record
    )

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
    # If high risk (R >= 70), dispatch emergency Telegram alert to all registered guardians
    if risk["score"] >= 70:
        bank_name = VIETNAM_BANKS.get(qr_data.bank_bin, f"Mã BIN: {qr_data.bank_bin}")
        guardian_chat_ids = get_guardians_for_phone(payload.elder_phone)
        
        for cid in guardian_chat_ids:
            sent = await send_scam_alert(
                bank_name=bank_name,
                account_number=qr_data.account_number,
                amount=qr_data.amount,
                message=qr_data.message,
                risk_score=risk["score"],
                risk_reason=risk["reason"],
                target_chat_id=cid
            )
            if sent:
                alert_triggered = True
    
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
