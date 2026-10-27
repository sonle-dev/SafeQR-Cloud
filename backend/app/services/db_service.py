import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from ..core.config import settings
import httpx

logger = logging.getLogger(__name__)

# Fallback in-memory store if database is offline during local test
_MEMORY_GUARDIANS: Dict[str, List[Dict[str, Any]]] = {
    "0912345678": [
        {
            "elder_name": "Bố Nguyễn Văn An",
            "guardian_name": "Sơn (Con trai)",
            "guardian_telegram_chat_id": "5456687635"
        }
    ]
}

def get_db_connection():
    if not settings.DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(settings.DATABASE_URL, connect_timeout=3)
        return conn
    except Exception as e:
        logger.warning(f"Không thể kết nối CSDL PostgreSQL ({e}). Sử dụng bộ đệm nội bộ.")
        return None

def register_guardian(
    elder_phone: str,
    elder_name: str,
    guardian_name: str,
    chat_id: str,
    guardian_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registers a guardian link in PostgreSQL (or in-memory cache).
    """
    cleaned_phone = elder_phone.strip()
    record = {
        "elder_phone": cleaned_phone,
        "elder_name": elder_name.strip(),
        "guardian_name": guardian_name.strip(),
        "guardian_telegram_chat_id": chat_id.strip(),
        "guardian_phone": guardian_phone.strip() if guardian_phone else ""
    }

    # Always update in-memory cache
    if cleaned_phone not in _MEMORY_GUARDIANS:
        _MEMORY_GUARDIANS[cleaned_phone] = []
    
    # Remove existing record with same chat_id if any
    _MEMORY_GUARDIANS[cleaned_phone] = [
        g for g in _MEMORY_GUARDIANS[cleaned_phone] 
        if g.get("guardian_telegram_chat_id") != chat_id.strip()
    ]
    _MEMORY_GUARDIANS[cleaned_phone].append(record)

    # Try persisting to PostgreSQL
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO guardians (elder_phone, elder_name, guardian_name, guardian_telegram_chat_id, guardian_phone, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (elder_phone, guardian_telegram_chat_id) 
                    DO UPDATE SET 
                        elder_name = EXCLUDED.elder_name,
                        guardian_name = EXCLUDED.guardian_name,
                        guardian_phone = EXCLUDED.guardian_phone,
                        is_active = TRUE;
                """, (cleaned_phone, record["elder_name"], record["guardian_name"], record["guardian_telegram_chat_id"], record["guardian_phone"]))
                conn.commit()
                logger.info(f"Đã lưu liên kết người bảo hộ vào PostgreSQL cho SĐT: {cleaned_phone}")
        except Exception as e:
            logger.error(f"Lỗi khi insert vào bảng guardians: {e}")
        finally:
            conn.close()

    return record

def get_guardians_for_phone(elder_phone: Optional[str]) -> List[str]:
    """
    Retrieves list of Telegram Chat IDs associated with an elder phone number.
    Returns default chat ID if not found or phone is empty.
    """
    if not elder_phone:
        return [settings.DEFAULT_GUARDIAN_CHAT_ID] if settings.DEFAULT_GUARDIAN_CHAT_ID else []

    cleaned_phone = elder_phone.strip()
    chat_ids = set()

    # Check PostgreSQL
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT guardian_telegram_chat_id 
                    FROM guardians 
                    WHERE elder_phone = %s AND is_active = TRUE;
                """, (cleaned_phone,))
                rows = cur.fetchall()
                for r in rows:
                    if r.get("guardian_telegram_chat_id"):
                        chat_ids.add(r["guardian_telegram_chat_id"])
        except Exception as e:
            logger.error(f"Lỗi truy vấn guardians từ PostgreSQL: {e}")
        finally:
            conn.close()

    # Check in-memory fallback
    if cleaned_phone in _MEMORY_GUARDIANS:
        for g in _MEMORY_GUARDIANS[cleaned_phone]:
            cid = g.get("guardian_telegram_chat_id")
            if cid:
                chat_ids.add(cid)

    # Fallback to default if no specific mapping found
    if not chat_ids and settings.DEFAULT_GUARDIAN_CHAT_ID:
        chat_ids.add(settings.DEFAULT_GUARDIAN_CHAT_ID)

    return list(chat_ids)

async def send_registration_confirmation(chat_id: str, elder_name: str, elder_phone: str, guardian_name: str) -> bool:
    """
    Sends a test verification message to the guardian upon self-declaration.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token or not chat_id:
        return False

    text = (
        "🎉 <b>LIÊN KẾT BẢO VỆ THÀNH CÔNG!</b>\n\n"
        f"Chào <b>{guardian_name}</b>, thiết bị của:\n"
        f"• <b>Người thân:</b> {elder_name}\n"
        f"• <b>Số điện thoại:</b> <code>{elder_phone}</code>\n\n"
        "🛡️ <i>Từ bây giờ, bất cứ khi nào người thân của bạn quét mã VietQR có dấu hiệu lừa đảo, "
        "hệ thống sẽ tự động khóa chuyển tiền và gửi báo động khẩn cấp tới đây ngay lập tức!</i>"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Lỗi gửi xác nhận đăng ký: {e}")
        return False
