import hmac
import html
import re
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.identity_service import link_telegram_chat
from app.services.telegram_bot import send_message, webhook_secret


router = APIRouter(prefix="/v1/telegram", tags=["Telegram"])
START = re.compile(r"^/start\s+([A-Za-z0-9_-]{16,64})$")


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    """Recibe los mensajes del bot. Siempre responde 200 para que Telegram no reintente."""
    if not x_telegram_bot_api_secret_token or not hmac.compare_digest(
        x_telegram_bot_api_secret_token, webhook_secret()
    ):
        return {"ok": False}
    try:
        update: dict[str, Any] = await request.json()
    except ValueError:
        return {"ok": True}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        return {"ok": True}
    chat_id = str(chat.get("id", ""))
    match = START.match(str(message.get("text", "")).strip())
    if not match:
        send_message(chat_id, "Hola. Para recibir tus avisos de ExpoNexo, vincula Telegram desde <b>Mi cuenta</b> en el portal.")
        return {"ok": True}
    user = link_telegram_chat(db, match.group(1), chat_id)
    if user is None:
        send_message(chat_id, "El enlace venció o ya se usó. Genera uno nuevo desde <b>Mi cuenta</b> en el portal.")
    else:
        send_message(
            chat_id,
            f"Listo, {html.escape(user.nombre)}: tu cuenta de ExpoNexo quedó vinculada. "
            "Aquí recibirás tus avisos de reservas, pagos, entradas, citas y soporte.",
        )
    return {"ok": True}
