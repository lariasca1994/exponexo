import base64
import io
import secrets
import time

import pyotp
import qrcode

from app.config import get_settings


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_provisioning_uri(secret: str, email: str) -> str:
    settings = get_settings()
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.mfa_issuer_name)


def generate_qr_data_url(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def verify_totp_code(
    secret: str,
    code: str,
    last_accepted_step: int | None,
    at_timestamp: float | None = None,
) -> tuple[bool, int | None]:
    """Verify a 6-digit TOTP code and enforce replay protection via time step."""
    cleaned = code.strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False, None

    now_ts = at_timestamp if at_timestamp is not None else time.time()
    totp = pyotp.TOTP(secret)
    current_step = int(now_ts // totp.interval)

    for offset in (-1, 0, 1):
        candidate_step = current_step + offset
        if last_accepted_step is not None and candidate_step <= last_accepted_step:
            continue
        candidate_time = candidate_step * totp.interval
        if totp.verify(cleaned, for_time=candidate_time, valid_window=0):
            return True, candidate_step

    return False, None


def generate_email_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_backup_codes(count: int = 8) -> list[str]:
    codes: list[str] = []
    for _ in range(count):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        codes.append(f"{part1}-{part2}")
    return codes
