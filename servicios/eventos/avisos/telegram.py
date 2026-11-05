import html
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("exponexo.eventos.avisos.telegram")


def telegram_text(title: str, message: str, link: str) -> str:
    """Mismo aviso que el correo, resumido para Telegram (solo admite negrita y enlaces)."""
    return (
        f"<b>{html.escape(title)}</b>\n\n{html.escape(message)}\n\n"
        f'<a href="{html.escape(link, quote=True)}">Abrir en ExpoNexo</a>'
    )


def send_telegram_message(
    chat_id: str,
    text: str,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Envía el aviso al chat que la persona vinculó desde su perfil."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token or not chat_id:
        logger.info("Modo local sin TELEGRAM_BOT_TOKEN o sin chat vinculado: aviso simulado")
        return {"modo": "simulado", "texto": text}

    own_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0)
    try:
        response = client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        )
        response.raise_for_status()
        return response.json()
    finally:
        if own_client:
            client.close()
