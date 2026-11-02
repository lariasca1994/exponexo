import base64
import hashlib
import hmac
import json
from typing import Any

from app.config import settings
from app.errors import ProblemDetailError


def _get_qr_secret_bytes() -> bytes:
    raw = (settings.ticket_qr_signing_key or "").strip()
    if not raw:
        return b"exponexo-entrada-qr-clave-desarrollo-32b"
    try:
        return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    except Exception:
        return raw.encode("utf-8")


def sign_ticket_qr(ticket_id: str, event_id: str, user_id: str, ticket_type: str) -> str:
    payload_obj = {
        "entrada_id": ticket_id,
        "evento_id": event_id,
        "usuario_id": user_id,
        "tipo": ticket_type,
        "v": 1,
    }
    payload_bytes = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")

    signature = hmac.new(
        _get_qr_secret_bytes(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    encoded_sig = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"EXN1.{encoded_payload}.{encoded_sig}"


def verify_ticket_qr(qr_token: str) -> dict[str, Any]:
    parts = (qr_token or "").strip().split(".")
    if len(parts) != 3 or parts[0] != "EXN1":
        raise ProblemDetailError(
            status=400,
            title="Código QR de entrada inválido",
            detail="El formato del código QR de la entrada no es válido.",
            problem_type="https://exponexo.co/problemas/qr-entrada-invalido",
        )

    encoded_payload, encoded_sig = parts[1], parts[2]
    expected_sig_bytes = hmac.new(
        _get_qr_secret_bytes(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    expected_sig = base64.urlsafe_b64encode(expected_sig_bytes).decode("ascii").rstrip("=")

    if not hmac.compare_digest(encoded_sig, expected_sig):
        raise ProblemDetailError(
            status=400,
            title="Firma de QR inválida",
            detail="La firma criptográfica del código QR de la entrada no coincide.",
            problem_type="https://exponexo.co/problemas/qr-firma-invalida",
        )

    try:
        padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(decoded.decode("utf-8"))
        if not isinstance(data, dict) or "entrada_id" not in data:
            raise ValueError("Payload incompleto")
        return data
    except Exception as exc:
        raise ProblemDetailError(
            status=400,
            title="Contenido de QR inválido",
            detail="No fue posible leer los datos del código QR de la entrada.",
            problem_type="https://exponexo.co/problemas/qr-contenido-invalido",
        ) from exc
