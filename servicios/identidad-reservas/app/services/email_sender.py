import logging

import httpx

from app.config import get_settings


logger = logging.getLogger("exponexo.email")

# In-memory mailbox for local development & automated tests when Brevo is not configured
_dev_outbox: list[dict[str, str]] = []


def get_last_dev_code(email: str, purpose: str | None = None) -> str | None:
    normalized = email.strip().lower()
    for item in reversed(_dev_outbox):
        if item["email"] == normalized and (purpose is None or item["purpose"] == purpose):
            return item["code"]
    return None


def clear_dev_outbox() -> None:
    _dev_outbox.clear()


def send_verification_email(email: str, name: str, code: str, purpose: str) -> None:
    settings = get_settings()
    _dev_outbox.append(
        {
            "email": email.strip().lower(),
            "name": name,
            "code": code,
            "purpose": purpose,
        }
    )
    if not settings.brevo_api_key:
        logger.info("Modo local sin BREVO_API_KEY: código enviado a %s (%s)", email, purpose)
        return

    try:
        httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.brevo_api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={
                "sender": {
                    "name": settings.brevo_sender_name,
                    "email": settings.brevo_sender_email,
                },
                "to": [{"email": email, "name": name}],
                "subject": f"ExpoNexo · Código de verificación ({purpose})",
                "htmlContent": (
                    f"<p>Hola {name},</p>"
                    f"<p>Tu código de verificación para <strong>{purpose}</strong> en ExpoNexo es:</p>"
                    f"<h2>{code}</h2>"
                    f"<p>Este código vence en {settings.mfa_email_code_minutes} minutos.</p>"
                ),
            },
            timeout=10.0,
        )
    except Exception as exc:
        logger.warning("No se pudo enviar correo por Brevo: %s", exc)
