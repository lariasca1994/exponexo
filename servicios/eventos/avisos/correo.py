import html
import logging
import os
import pathlib
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("exponexo.eventos.avisos.correo")

FORBIDDEN_SENSITIVE_KEYS = {
    "contrasena",
    "password",
    "codigo_mfa",
    "secreto_totp",
    "tarjeta",
    "cvv",
    "pan",
    "token_acceso",
    "token_refresco",
}

TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent / "plantillas"


def render_template(title: str, message: str, portal_link: str) -> tuple[str, str]:
    html_raw = (TEMPLATE_DIR / "base.html").read_text(encoding="utf-8")
    txt_raw = (TEMPLATE_DIR / "base.txt").read_text(encoding="utf-8")
    # El logo del portal: en los correos solo se ven bien las imagenes PNG.
    origen = urlparse(portal_link)
    logo = f"{origen.scheme}://{origen.netloc}/apple-touch-icon.png"
    replacements = {
        "{{titulo}}": title,
        "{{mensaje}}": message,
        "{{enlace_portal}}": portal_link,
    }
    # En el HTML los valores se escapan: el mensaje lleva datos del usuario (su nombre).
    for placeholder, val in replacements.items():
        html_raw = html_raw.replace(placeholder, html.escape(val))
        txt_raw = txt_raw.replace(placeholder, val)
    html_raw = html_raw.replace("{{logo}}", html.escape(logo))
    return html_raw, txt_raw


def assert_no_sensitive_data(data: dict[str, Any]) -> None:
    lowered = {str(k).lower() for k in data.keys()}
    forbidden = lowered.intersection(FORBIDDEN_SENSITIVE_KEYS)
    if forbidden:
        raise ValueError(f"Datos sensibles prohibidos en aviso por correo: {sorted(forbidden)}")


def send_brevo_email(
    recipient_email: str,
    recipient_name: str,
    subject: str,
    html_content: str,
    text_content: str,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("BREVO_REMITENTE_CORREO", "avisos@exponexo.co").strip() or "avisos@exponexo.co"
    sender_name = os.getenv("BREVO_REMITENTE_NOMBRE", "ExpoNexo").strip() or "ExpoNexo"

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": recipient_email, "name": recipient_name or recipient_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    if not api_key:
        logger.info("Modo local sin BREVO_API_KEY: correo simulado para %s (%s)", recipient_email, subject)
        return {"modo": "simulado", "destinatario": recipient_email, "asunto": subject}

    own_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0)
    try:
        response = client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    finally:
        if own_client:
            client.close()
