import re
from typing import Tuple, List, Dict, Any

# Keywords indicating governmental, public fine, legal authority or impersonation
GOVERNMENT_KEYWORDS = [
    "nop phat", "phat nguoi", "vneid", "cong an", "vien kiem sat",
    "toa an", "an phi", "tam giu", "dieu tra", "lenh bat", "khoi to",
    "cuc thue", "bao hiem xa hoi", "dinh danh", "truy na", "phat giao thong"
]

def check_semantic_conflict(message: str, is_personal_account: bool = True) -> Tuple[bool, int, List[str]]:
    """
    Checks if transaction purpose claims to be official/legal fine/public authority
    while the beneficiary is a personal bank account.
    """
    cleaned = re.sub(r'[\.\-\_\s]+', ' ', message.lower()).strip()
    detected_keywords = []
    
    for kw in GOVERNMENT_KEYWORDS:
        if kw in cleaned:
            detected_keywords.append(kw)
            
    has_conflict = len(detected_keywords) > 0 and is_personal_account
    conflict_score = 100 if has_conflict else 0
    return has_conflict, conflict_score, detected_keywords


def calculate_risk_score(
    conflict_score: int,      # S_conflict (0 or 100)
    ml_probability: float,    # P_ML (0.0 to 1.0)
    velocity_count: int,      # Number of scans in the last hour
    is_blacklisted: bool      # B_blacklist
) -> Dict[str, Any]:
    """
    Calculates combined risk score R in [0, 100] based on formula:
    R = min(100, w1 * S_conflict + w2 * (P_ML * 100) + w3 * S_velocity + B_blacklist)
    w1 = 0.40, w2 = 0.35, w3 = 0.25
    """
    if is_blacklisted:
        return {
            "score": 100,
            "level": "HIGH_RISK",
            "action": "BLOCK_TRANSACTION",
            "reason": "Tài khoản thụ hưởng nằm trong Danh sách đen lừa đảo đã xác thực!"
        }
        
    w1, w2, w3 = 0.45, 0.35, 0.20
    
    # S_velocity: 0 if <= 2 scans, ramps up to 100 if >= 10 scans
    if velocity_count <= 2:
        s_velocity = 0
    elif velocity_count >= 10:
        s_velocity = 100
    else:
        s_velocity = int(((velocity_count - 2) / 8.0) * 100)
        
    raw_r = (w1 * conflict_score) + (w2 * (ml_probability * 100)) + (w3 * s_velocity)
    
    # If explicit public authority conflict is detected and ML agrees, elevate to High Risk
    if conflict_score >= 100 and ml_probability >= 0.5:
        raw_r = max(raw_r, 75.0)

    r = min(100, int(round(raw_r)))
    
    if r < 35:
        level = "SAFE"
        action = "ALLOW"
        reason = "Giao dịch bình thường, không phát hiện dấu hiệu lừa đảo."
    elif r < 70:
        level = "SUSPICIOUS"
        action = "WARNING"
        reason = "Cảnh báo: Tài khoản nhận tiền cá nhân hoặc nội dung có yếu tố cần xác thực lại."
    else:
        level = "HIGH_RISK"
        action = "BLOCK_TRANSACTION"
        reason = "NGUY HIỂM: Phát hiện dấu hiệu mạo danh công quyền hoặc thao túng tâm lý chiếm đoạt tài sản!"
        
    return {
        "score": r,
        "level": level,
        "action": action,
        "reason": reason,
        "details": {
            "conflict_score": conflict_score,
            "ml_probability": round(ml_probability, 4),
            "velocity_score": s_velocity,
            "velocity_count": velocity_count
        }
    }
