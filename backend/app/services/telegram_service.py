import httpx
import logging
from typing import Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

async def send_scam_alert(
    bank_name: str,
    account_number: str,
    amount: Optional[float],
    message: str,
    risk_score: int,
    risk_reason: str,
    target_chat_id: Optional[str] = None
) -> bool:
    """
    Sends real-time emergency alert via Telegram Bot to guardian / relatives.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = target_chat_id or settings.DEFAULT_GUARDIAN_CHAT_ID

    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token hoặc Chat ID chưa được cấu hình. Bỏ qua gửi thông báo.")
        return False

    amount_str = f"{int(amount):,} VNĐ" if amount else "Không chỉ định (Mã tĩnh)"

    text = (
        "🚨 <b>CẢNH BÁO KHẨN CẤP: PHÁT HIỆN VIETQR LỪA ĐẢO!</b>\n\n"
        "Hệ thống SafeQR vừa phát hiện một giao dịch có dấu hiệu thao túng tâm lý:\n"
        f"• <b>Mức độ rủi ro:</b> {risk_score}/100 (BÁO ĐỘNG ĐỎ)\n"
        f"• <b>Ngân hàng thụ hưởng:</b> {bank_name}\n"
        f"• <b>Số tài khoản:</b> <code>{account_number}</code>\n"
        f"• <b>Số tiền:</b> {amount_str}\n"
        f"• <b>Nội dung bẫy:</b> <i>{message or 'Không có'}</i>\n\n"
        f"⚠️ <b>Lý do cảnh báo:</b> {risk_reason}\n"
        "🛑 <b>Hành động hệ thống:</b> Đã KHÓA nút chuyển tiền trên màn hình ứng dụng.\n"
        "👉 <i>Vui lòng gọi điện ngay cho người thân để ngăn chặn kịp thời!</i>"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Đã gửi cảnh báo Telegram thành công tới Chat ID: {chat_id}")
                return True
            else:
                logger.error(f"Gửi cảnh báo Telegram thất bại ({resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Lỗi kết nối tới Telegram API: {e}")
        return False
