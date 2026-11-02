import json
import logging
import os
from typing import Any

import httpx

from avisos.correo import assert_no_sensitive_data, render_template, send_brevo_email
from avisos.telegram import send_telegram_alert

logger = logging.getLogger("exponexo.eventos.avisos")
logger.setLevel(logging.INFO)

# Registro en memoria por contenedor de Lambda para idempotencia de avisos repetidos
_PROCESSED_EVENT_IDS: set[str] = set()


def reset_processed_events() -> None:
    _PROCESSED_EVENT_IDS.clear()


def _extract_envelope(raw_body: str) -> dict[str, Any]:
    parsed = json.loads(raw_body)
    if isinstance(parsed, dict) and parsed.get("Type") == "Notification" and "Message" in parsed:
        return json.loads(parsed["Message"])
    return parsed


def process_notification_envelope(
    envelope: dict[str, Any],
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    event_id = str(envelope.get("id", "")).strip()
    if not event_id:
        raise ValueError("El evento no tiene identificador 'id'")

    if event_id in _PROCESSED_EVENT_IDS:
        return {"estado": "duplicado_ignorado", "evento_id": event_id}

    event_type = str(envelope.get("tipo", ""))
    data = envelope.get("datos") or {}
    assert_no_sensitive_data(data)

    portal_url = os.getenv("PORTAL_URL", "http://localhost:5173").rstrip("/")
    result: dict[str, Any] = {"estado": "procesado", "evento_id": event_id, "tipo": event_type}

    if event_type == "cuenta.creada":
        email = str(data.get("correo", "expositor@exponexo.co"))
        name = str(data.get("nombre", "Participante"))
        html_body, txt_body = render_template(
            title="Te damos la bienvenida a ExpoNexo",
            message=f"Hola {name}, tu cuenta en ExpoNexo fue creada exitosamente. Ya puedes explorar el catálogo de ferias, reservar stands o adquirir entradas.",
            portal_link=f"{portal_url}/eventos",
        )
        send_brevo_email(email, name, "Te damos la bienvenida a ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "reserva.creada":
        email = str(data.get("correo", "expositor@exponexo.co"))
        reserva_id = str(data.get("reserva", ""))
        vence_en = str(data.get("vence_en", ""))
        html_body, txt_body = render_template(
            title="Reserva temporal de stand registrada",
            message=f"Registramos tu reserva {reserva_id}. Recuerda completar el pago antes de {vence_en} para confirmar tu stand.",
            portal_link=f"{portal_url}/mis-reservas",
        )
        send_brevo_email(email, "Expositor", "Reserva temporal de stand · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "reserva.vencida":
        email = str(data.get("correo", "expositor@exponexo.co"))
        reserva_id = str(data.get("reserva", ""))
        html_body, txt_body = render_template(
            title="Tu reserva temporal venció",
            message=f"La reserva {reserva_id} expiró sin pago registrado y el stand volvió a estar disponible.",
            portal_link=f"{portal_url}/eventos",
        )
        send_brevo_email(email, "Expositor", "Reserva vencida · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "reserva.pagada":
        email = str(data.get("correo", "expositor@exponexo.co"))
        reserva_id = str(data.get("reserva", ""))
        html_body, txt_body = render_template(
            title="Stand confirmado en ExpoNexo",
            message=f"Tu reserva {reserva_id} quedó confirmada y pagada. Nos vemos en el recinto ferial.",
            portal_link=f"{portal_url}/mis-reservas",
        )
        send_brevo_email(email, "Expositor", "Stand confirmado · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "pago.aprobado":
        email = str(data.get("correo", "comprador@exponexo.co"))
        factura = str(data.get("factura", ""))
        orden = str(data.get("orden", ""))
        html_body, txt_body = render_template(
            title=f"Factura electrónica {factura} disponible",
            message=f"Tu pago de la orden {orden} fue aprobado y se emitió la factura {factura}. Puedes consultarla en tu portal.",
            portal_link=f"{portal_url}/mis-facturas",
        )
        send_brevo_email(email, "Comprador", f"Factura {factura} · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "pago.rechazado":
        email = str(data.get("correo", "comprador@exponexo.co"))
        orden = str(data.get("orden", ""))
        motivo = str(data.get("motivo", "Transacción rechazada"))
        html_body, txt_body = render_template(
            title="Tu intento de pago no pudo completarse",
            message=f"La orden {orden} registró un intento rechazado ({motivo}). Puedes generar un nuevo intento desde el portal.",
            portal_link=f"{portal_url}/pagos/orden/{orden}",
        )
        send_brevo_email(email, "Comprador", "Aviso sobre tu orden de pago · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "pago.reembolsado":
        email = str(data.get("correo", "comprador@exponexo.co"))
        orden = str(data.get("orden", ""))
        html_body, txt_body = render_template(
            title="Reembolso registrado en ExpoNexo",
            message=f"Se procesó el reembolso asociado a la orden {orden}. Puedes revisar el estado actualizado en tus facturas.",
            portal_link=f"{portal_url}/mis-facturas",
        )
        send_brevo_email(email, "Comprador", "Reembolso registrado · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "entrada.activada":
        email = str(data.get("correo", "visitante@exponexo.co"))
        entrada_id = str(data.get("entrada", ""))
        html_body, txt_body = render_template(
            title="Tu entrada para ExpoNexo está activa",
            message=f"Tu entrada {entrada_id} ya está activa. Ábrela desde el portal para presentar tu código QR firmado en el ingreso.",
            portal_link=f"{portal_url}/mis-entradas",
        )
        send_brevo_email(email, "Visitante", "Tu entrada QR · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "cita.aceptada":
        participantes = data.get("participantes") or ["participante@exponexo.co"]
        cita_id = str(data.get("cita", ""))
        inicio = str(data.get("inicio", ""))
        fin = str(data.get("fin", ""))
        html_body, txt_body = render_template(
            title="Cita de negocios confirmada",
            message=f"La cita {cita_id} quedó programada de {inicio} a {fin}. Consulta la sala asignada en tu agenda.",
            portal_link=f"{portal_url}/agenda",
        )
        for addr in participantes:
            email_addr = str(addr) if "@" in str(addr) else f"{addr}@exponexo.co"
            send_brevo_email(email_addr, "Participante", "Cita de negocios confirmada · ExpoNexo", html_body, txt_body, http_client)
        result["canal"] = "correo"

    elif event_type == "ticket.creado":
        prioridad = str(data.get("prioridad", "")).lower()
        if prioridad in {"alta", "critica"}:
            ticket_id = str(data.get("ticket", ""))
            ubicacion = str(data.get("ubicacion", "Recinto"))
            send_telegram_alert(
                f"[ExpoNexo · Prioridad {prioridad.upper()}] Nuevo ticket {ticket_id} en {ubicacion}.",
                http_client=http_client,
            )
            result["canal"] = "telegram"
        else:
            result["canal"] = "ninguno_prioridad_baja"

    elif event_type == "ticket.sla_vencido":
        ticket_id = str(data.get("ticket", ""))
        nivel = str(data.get("nivel", "1"))
        send_telegram_alert(
            f"[ExpoNexo · SLA VENCIDO] El ticket {ticket_id} superó el acuerdo de atención (escalamiento nivel {nivel}).",
            http_client=http_client,
        )
        result["canal"] = "telegram"

    elif event_type == "dispositivo.caido":
        dispositivo = str(data.get("dispositivo", ""))
        ubicacion = str(data.get("ubicacion", "Recinto"))
        ticket_id = str(data.get("ticket", ""))
        send_telegram_alert(
            f"[ExpoNexo · DISPOSITIVO CAÍDO] Kiosco/pantalla {dispositivo} sin reporte en {ubicacion} (ticket {ticket_id}).",
            http_client=http_client,
        )
        result["canal"] = "telegram"

    else:
        result["canal"] = "ignorado"

    _PROCESSED_EVENT_IDS.add(event_id)
    return result


def handler(
    event: dict[str, Any],
    context: Any = None,
    http_client: httpx.Client | None = None,
) -> dict[str, list[dict[str, str]]]:
    """
    Punto de entrada AWS Lambda para SQS con respuesta parcial de lote (ReportBatchItemFailures).
    """
    records = event.get("Records") or []
    failures: list[dict[str, str]] = []

    for record in records:
        message_id = str(record.get("messageId", ""))
        try:
            envelope = _extract_envelope(str(record.get("body", "{}")))
            process_notification_envelope(envelope, http_client=http_client)
        except Exception as exc:
            logger.error("Fallo al procesar aviso del mensaje %s: %s", message_id, exc)
            if message_id:
                failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
