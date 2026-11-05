"""Bot de Telegram de ExpoNexo: vinculación del chat de cada persona y mensajes de confirmación.

La vinculación no consulta Telegram periódicamente (eso mantendría despierta la base): la persona
abre el enlace del bot desde su perfil, pulsa «Iniciar» y Telegram entrega ese mensaje al webhook
de este servicio, que guarda su chat. El webhook solo acepta peticiones con el token secreto
derivado de INTERNO_SECRETO, que el workflow registra en Telegram al desplegar.
"""
import hashlib
import logging
from functools import lru_cache

import httpx

from app.config import get_settings

logger = logging.getLogger("exponexo.identidad.telegram")
API = "https://api.telegram.org"


def webhook_secret(internal_secret: str | None = None) -> str:
    """Token que Telegram envía en X-Telegram-Bot-Api-Secret-Token (mismo cálculo que el workflow)."""
    base = internal_secret if internal_secret is not None else get_settings().internal_secret
    return hashlib.sha256(f"telegram:{base}".encode()).hexdigest()[:48]


@lru_cache(maxsize=1)
def bot_username() -> str | None:
    token = get_settings().telegram_bot_token.strip()
    if not token:
        return None
    try:
        respuesta = httpx.get(f"{API}/bot{token}/getMe", timeout=10.0)
        respuesta.raise_for_status()
        return respuesta.json()["result"]["username"]
    except Exception as exc:  # pragma: no cover - red externa
        logger.error("No se pudo consultar el bot de Telegram: %s", type(exc).__name__)
        return None


def send_message(chat_id: str, text: str) -> bool:
    token = get_settings().telegram_bot_token.strip()
    if not token or not chat_id:
        logger.info("Telegram sin configurar: mensaje simulado")
        return False
    try:
        respuesta = httpx.post(
            f"{API}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10.0,
        )
        return respuesta.is_success
    except Exception as exc:  # pragma: no cover - red externa
        logger.error("No se pudo enviar el mensaje de Telegram: %s", type(exc).__name__)
        return False
