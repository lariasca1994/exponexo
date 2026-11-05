import json
import logging
import os
from typing import Any, Callable

import httpx

from repartidor.rutas import InternalRouteTarget, resolve_route

logger = logging.getLogger("exponexo.eventos.repartidor")
logger.setLevel(logging.INFO)


def _extract_envelope(raw_body: str) -> dict[str, Any]:
    parsed = json.loads(raw_body)
    # Soporta mensaje directo de SQS o sobre de SNS fan-out (Type == Notification)
    if isinstance(parsed, dict) and parsed.get("Type") == "Notification" and "Message" in parsed:
        return json.loads(parsed["Message"])
    return parsed


def _obtain_service_jwt(http_client: httpx.Client, identidad_url: str, interno_secreto: str) -> str:
    response = http_client.post(
        f"{identidad_url.rstrip('/')}/v1/sesion/servicio",
        json={"servicio": "eventos-repartidor", "secreto_interno": interno_secreto},
        # Identidad escala a cero: la primera llamada puede esperar a que despierte
        timeout=60.0,
    )
    response.raise_for_status()
    return str(response.json()["token_servicio"])


def dispatch_envelope(
    envelope: dict[str, Any],
    http_client: httpx.Client | None = None,
    base_urls: dict[str, str] | None = None,
    service_token: str | None = None,
) -> InternalRouteTarget | None:
    target = resolve_route(envelope, base_urls=base_urls)
    if target is None:
        return None

    identidad_url = (base_urls or {}).get(
        "identidad-reservas",
        os.getenv("IDENTIDAD_URL", "http://localhost:8001"),
    )
    interno_secreto = os.getenv("INTERNO_SECRETO", "secreto-interno-desarrollo")
    correlation_id = str(envelope.get("correlacion_id") or envelope.get("id") or "")

    own_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0)
    try:
        token = service_token or _obtain_service_jwt(client, identidad_url, interno_secreto)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Correlacion-Id": correlation_id,
            "Content-Type": "application/json",
        }
        response = client.request(
            method=target.method,
            url=target.url,
            headers=headers,
            json=target.payload,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Error {response.status_code} al invocar {target.url}: {response.text}"
            )
        return target
    finally:
        if own_client:
            client.close()


def handler(
    event: dict[str, Any],
    context: Any = None,
    dispatcher: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """
    Punto de entrada AWS Lambda para SQS con respuesta parcial de lote (ReportBatchItemFailures).
    """
    records = event.get("Records") or []
    failures: list[dict[str, str]] = []
    dispatch_fn = dispatcher or dispatch_envelope

    for record in records:
        message_id = str(record.get("messageId", ""))
        try:
            envelope = _extract_envelope(str(record.get("body", "{}")))
            logger.info(
                "Procesando evento en repartidor",
                extra={
                    "evento_id": envelope.get("id"),
                    "tipo": envelope.get("tipo"),
                    "correlacion_id": envelope.get("correlacion_id"),
                },
            )
            dispatch_fn(envelope)
        except Exception as exc:
            logger.error(
                "Fallo al repartir mensaje SQS %s: %s",
                message_id,
                exc,
            )
            if message_id:
                failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
