from typing import Dict, Any, Optional
from ..core.crc16 import verify_crc16

def parse_tlv(raw_text: str) -> Dict[str, str]:
    """
    Parses a raw EMVCo TLV string into a key-value dictionary.
    Each element has Tag (2 digits), Length (2 digits), and Value.
    """
    elements: Dict[str, str] = {}
    i = 0
    length_raw = len(raw_text)
    
    while i + 4 <= length_raw:
        tag = raw_text[i:i+2]
        try:
            val_len = int(raw_text[i+2:i+4])
        except ValueError:
            break
        
        start_val = i + 4
        end_val = start_val + val_len
        if end_val > length_raw:
            break
            
        value = raw_text[start_val:end_val]
        elements[tag] = value
        i = end_val
        
    return elements


class VietQRData:
    def __init__(self, raw: str):
        self.raw = raw
        self.is_valid_crc = verify_crc16(raw)
        self.root_tags = parse_tlv(raw)
        
        # 00: Format indicator, 01: QR type (11 dynamic, 12 static)
        self.payload_format = self.root_tags.get("00", "")
        self.initiation_method = self.root_tags.get("01", "")
        
        # Tag 38: Napas / VietQR Merchant Account Info
        self.tag_38_raw = self.root_tags.get("38", "")
        self.bank_bin = ""
        self.account_number = ""
        self._parse_tag_38()
        
        # Tag 53: Currency, Tag 54: Amount
        self.currency = self.root_tags.get("53", "")
        self.amount: Optional[float] = None
        if "54" in self.root_tags:
            try:
                self.amount = float(self.root_tags["54"])
            except ValueError:
                self.amount = None
                
        # Tag 58: Country Code
        self.country_code = self.root_tags.get("58", "")
        
        # Tag 62: Additional Data Field (Message / Purpose)
        self.tag_62_raw = self.root_tags.get("62", "")
        self.message = ""
        self._parse_tag_62()
        
        # Tag 63: CRC
        self.crc = self.root_tags.get("63", "")

    def _parse_tag_38(self):
        if not self.tag_38_raw:
            return
        sub_tags = parse_tlv(self.tag_38_raw)
        
        # In VietQR, sub-tag 01 often contains beneficiary info:
        # nested 00: Bank BIN (6 digits), 01: Account Number
        sub_01 = sub_tags.get("01", "")
        if sub_01:
            nested = parse_tlv(sub_01)
            self.bank_bin = nested.get("00", "")
            self.account_number = nested.get("01", "")
        else:
            # Fallback if directly structured
            self.bank_bin = sub_tags.get("00", "")
            self.account_number = sub_tags.get("02", "")

    def _parse_tag_62(self):
        if not self.tag_62_raw:
            return
        sub_tags = parse_tlv(self.tag_62_raw)
        # Sub-tag 08 is transaction purpose / note in VietQR
        self.message = sub_tags.get("08", "")
        if not self.message:
            # Check other common sub-tags (01: Bill number, 07: Reference)
            self.message = sub_tags.get("01", "") or sub_tags.get("07", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid_crc": self.is_valid_crc,
            "bank_bin": self.bank_bin,
            "account_number": self.account_number,
            "amount": self.amount,
            "message": self.message,
            "currency": self.currency,
            "country_code": self.country_code,
            "initiation_method": self.initiation_method
        }
