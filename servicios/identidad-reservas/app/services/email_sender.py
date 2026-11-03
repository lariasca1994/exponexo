import html
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


def correo_codigo(name: str, code: str, purpose: str, minutes: int, portal_url: str) -> str:
    """Correo del código con los colores del portal (portal/src/estilos/tokens.css)."""
    logo = html.escape(f"{portal_url.rstrip('/')}/apple-touch-icon.png")
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Código de verificación · ExpoNexo</title></head>"
        '<body style="margin:0;padding:0;background:#f8fafc;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:24px 12px;"><tr><td align="center">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;'
        "border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;font-family:Inter,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#0f172a;\">"
        '<tr><td style="background:#e0f2fe;border-top:4px solid #0284c7;padding:16px 28px;">'
        f'<img src="{logo}" width="28" height="28" alt="" style="vertical-align:middle;border:0;border-radius:6px;margin-right:10px;">'
        '<span style="vertical-align:middle;font-size:17px;font-weight:700;color:#0f172a;">ExpoNexo</span>'
        '<span style="vertical-align:middle;font-size:13px;color:#475569;"> · Recinto Ferial</span></td></tr>'
        '<tr><td style="padding:24px 28px 8px;font-size:15px;line-height:1.6;color:#475569;">'
        f'<p style="margin:0 0 12px;">Hola {html.escape(name)},</p>'
        f'<p style="margin:0 0 16px;">Tu código de verificación para <strong style="color:#0f172a;">{html.escape(purpose)}</strong> en ExpoNexo es:</p>'
        f'<p style="margin:0 0 16px;font-size:30px;font-weight:700;letter-spacing:8px;color:#0284c7;">{html.escape(code)}</p>'
        f'<p style="margin:0 0 16px;">Vence en {minutes} minutos y sirve una sola vez. Si no lo pediste, ignora este correo.</p>'
        "</td></tr>"
        '<tr><td style="padding:16px 28px 22px;border-top:1px solid #e2e8f0;font-size:12px;line-height:1.5;color:#64748b;">'
        "ExpoNexo nunca te pedirá este código por teléfono, chat ni otro correo."
        "</td></tr></table></td></tr></table></body></html>"
    )


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
                "htmlContent": correo_codigo(
                    name, code, purpose, settings.mfa_email_code_minutes, settings.portal_url
                ),
            },
            timeout=10.0,
        )
    except Exception as exc:
        logger.warning("No se pudo enviar correo por Brevo: %s", exc)
