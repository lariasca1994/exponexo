import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("exponexo.eventos.avisos.telegram")


def send_telegram_alert(
    message_text: str,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        logger.info("Modo local sin TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID: alerta simulada -> %s", message_text)
        return {"modo": "simulado", "texto": message_text}

    own_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0)
    try:
        response = client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message_text,
            },
        )
        response.raise_for_status()
        return response.json()
    finally:
        if own_client:
            client.close()
