"""
EMVCo CRC-16 (CCITT-FALSE) Implementation.
Standard: Polynomial 0x1021, Initial value 0xFFFF, RefIn=False, RefOut=False, XorOut=0x0000.
"""

def calculate_crc16(payload: str) -> str:
    """
    Computes CRC-16/CCITT-FALSE checksum for a string.
    Returns 4-character uppercase hexadecimal string.
    """
    crc = 0xFFFF
    for char in payload.encode('ascii', errors='ignore'):
        crc ^= (char << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def verify_crc16(raw_qr: str) -> bool:
    """
    Verifies EMVCo CRC-16 checksum.
    The string must contain tag 63 followed by length 04 and a 4-hex checksum at the end.
    Example ending: ...6304ABCD
    """
    if len(raw_qr) < 8:
        return False
    
    idx_63 = raw_qr.rfind("6304")
    if idx_63 == -1 or idx_63 + 8 != len(raw_qr):
        return False
    
    payload_to_check = raw_qr[:idx_63 + 4]
    expected_crc = raw_qr[idx_63 + 4:idx_63 + 8].upper()
    calculated = calculate_crc16(payload_to_check)
    return calculated == expected_crc
