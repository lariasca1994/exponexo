"""Destinatarios de los avisos, leídos de la base de identidad en el momento de enviar.

Los correos y chats de Telegram nunca viven en la configuración: el evento trae a quién afecta
(identificadores, correos o roles) e identidad devuelve sus datos de contacto actuales.
"""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("exponexo.eventos.avisos.contactos")


def _service_token(client: httpx.Client, identidad_url: str, secreto: str) -> str:
    respuesta = client.post(
        f"{identidad_url}/v1/sesion/servicio",
        json={"servicio": "eventos-avisos", "secreto_interno": secreto},
    )
    respuesta.raise_for_status()
    return str(respuesta.json()["token_servicio"])


def resolve_contacts(
    ids: list[str] | None = None,
    correos: list[str] | None = None,
    roles: list[str] | None = None,
    http_client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    ids = [i for i in (ids or []) if i]
    correos = [c for c in (correos or []) if c and "@" in c]
    roles = [r for r in (roles or []) if r]
    if not (ids or correos or roles):
        return []

    identidad_url = os.getenv("IDENTIDAD_URL", "").strip().rstrip("/")
    secreto = os.getenv("INTERNO_SECRETO", "").strip()
    if not identidad_url or not secreto:
        # Modo local (pruebas): solo los correos que trae el evento, sin Telegram
        logger.info("Modo local sin IDENTIDAD_URL/INTERNO_SECRETO: destinatarios del evento")
        return [{"correo": c, "nombre": "", "telegram_chat_id": None} for c in correos]

    own_client = http_client is None
    # Identidad escala a cero: la primera llamada puede esperar a que despierte
    client = http_client or httpx.Client(timeout=60.0)
    try:
        token = _service_token(client, identidad_url, secreto)
        respuesta = client.get(
            f"{identidad_url}/v1/interno/contactos",
            params={"ids": ",".join(ids), "correos": ",".join(correos), "roles": ",".join(roles)},
            headers={"Authorization": f"Bearer {token}"},
        )
        respuesta.raise_for_status()
        contactos = respuesta.json()
    finally:
        if own_client:
            client.close()

    unicos: dict[str, dict[str, Any]] = {}
    for contacto in contactos:
        unicos.setdefault(str(contacto.get("correo", "")).lower(), contacto)
    return list(unicos.values())
