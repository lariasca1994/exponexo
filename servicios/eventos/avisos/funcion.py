import json
import logging
import os
from typing import Any

import httpx

from avisos.correo import assert_no_sensitive_data, render_template, send_brevo_email
from avisos.contactos import resolve_contacts
from avisos.telegram import send_telegram_message, telegram_text

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


def _ids(data: dict[str, Any], *keys: str) -> list[str]:
    return [str(data[k]) for k in keys if data.get(k)]


def _aviso(event_type: str, data: dict[str, Any], portal_url: str) -> dict[str, Any] | None:
    """Qué decir y a quién: ids, correos o roles de las personas afectadas (se resuelven en la BD)."""

    def d(*keys: str) -> str:
        return next((str(data[k]) for k in keys if data.get(k)), "")

    persona = {"ids": _ids(data, "usuario_id", "usuario"), "correos": [d("correo")] if d("correo") else []}

    if event_type == "cuenta.creada":
        nombre = d("nombre") or "participante"
        return {**persona, "asunto": "Te damos la bienvenida a ExpoNexo", "titulo": "Te damos la bienvenida a ExpoNexo",
                "mensaje": f"Hola {nombre}, tu cuenta en ExpoNexo fue creada. Ya puedes explorar las ferias, reservar "
                           "stands o adquirir entradas. Vincula tu Telegram desde Mi cuenta para recibir también ahí tus avisos.",
                "enlace": f"{portal_url}/eventos"}
    if event_type == "cuenta.contrasena_cambiada":
        return {**persona, "asunto": "Tu contraseña cambió · ExpoNexo", "titulo": "Tu contraseña cambió",
                "mensaje": "La contraseña de tu cuenta se cambió y se cerraron tus sesiones en otros dispositivos. "
                           "Si no fuiste tú, restablécela de inmediato desde «¿Olvidaste tu contraseña?».",
                "enlace": f"{portal_url}/recuperar"}
    if event_type == "cuenta.contrasena_restablecida":
        return {**persona, "asunto": "Contraseña restablecida · ExpoNexo", "titulo": "Restableciste tu contraseña",
                "mensaje": "Tu contraseña se restableció con el código enviado a tu correo y se cerraron todas tus "
                           "sesiones. Si no fuiste tú, restablécela de nuevo y revisa la seguridad de tu correo.",
                "enlace": f"{portal_url}/ingreso"}
    if event_type == "reserva.creada":
        return {**persona, "asunto": "Reserva temporal de stand · ExpoNexo", "titulo": "Reserva temporal de stand registrada",
                "mensaje": f"Registramos tu reserva {d('reserva_id', 'reserva')}. Completa el pago antes de "
                           f"{d('vence_en')} para confirmar tu stand.",
                "enlace": f"{portal_url}/reservas"}
    if event_type == "reserva.vencida":
        return {**persona, "asunto": "Reserva vencida · ExpoNexo", "titulo": "Tu reserva temporal venció",
                "mensaje": f"La reserva {d('reserva_id', 'reserva')} venció sin pago y el stand volvió a quedar disponible.",
                "enlace": f"{portal_url}/eventos"}
    if event_type == "reserva.pagada":
        return {**persona, "asunto": "Stand confirmado · ExpoNexo", "titulo": "Stand confirmado en ExpoNexo",
                "mensaje": f"Tu reserva {d('reserva_id', 'reserva')} quedó pagada y confirmada. Nos vemos en el recinto.",
                "enlace": f"{portal_url}/reservas"}
    if event_type == "pago.aprobado":
        factura = d("numero_factura", "factura")
        return {**persona, "asunto": f"Factura {factura} · ExpoNexo", "titulo": f"Factura electrónica {factura} disponible",
                "mensaje": f"Tu pago de la orden {d('orden_id', 'orden')} fue aprobado y se emitió la factura {factura}.",
                "enlace": f"{portal_url}/facturas"}
    if event_type == "pago.rechazado":
        return {**persona, "asunto": "Aviso sobre tu orden de pago · ExpoNexo", "titulo": "Tu intento de pago no se completó",
                "mensaje": f"La orden {d('orden_id', 'orden')} registró un intento rechazado "
                           f"({d('motivo') or 'transacción rechazada'}). Puedes intentarlo de nuevo desde el portal.",
                "enlace": f"{portal_url}/facturas"}
    if event_type == "pago.reembolsado":
        return {**persona, "asunto": "Reembolso registrado · ExpoNexo", "titulo": "Reembolso registrado",
                "mensaje": f"Se procesó el reembolso de la orden {d('orden_id', 'orden')}. Revisa el estado en tus facturas.",
                "enlace": f"{portal_url}/facturas"}
    if event_type == "entrada.activada":
        return {**persona, "asunto": "Tu entrada QR · ExpoNexo", "titulo": "Tu entrada está activa",
                "mensaje": f"Tu entrada {d('entrada')} ya está activa. Ábrela en el portal para presentar tu código QR "
                           "en el ingreso.",
                "enlace": f"{portal_url}/mis-entradas"}
    if event_type == "cita.aceptada":
        participantes = [str(p) for p in (data.get("participantes") or [])]
        return {"ids": [p for p in participantes if "@" not in p], "correos": [p for p in participantes if "@" in p],
                "asunto": "Cita de negocios confirmada · ExpoNexo", "titulo": "Cita de negocios confirmada",
                "mensaje": f"Tu cita quedó programada de {d('inicio')} a {d('fin')} en la sala {d('sala')}.",
                "enlace": f"{portal_url}/agenda"}
    if event_type == "ticket.creado":
        prioridad = d("prioridad").lower()
        urgente = prioridad in {"alta", "critica"}
        return {**persona, "roles": ["personal", "administrador"] if urgente else [],
                "asunto": f"Ticket {d('ticket')} registrado · ExpoNexo", "titulo": f"Ticket {d('ticket')} registrado",
                "mensaje": f"Se registró el ticket {d('ticket')} con prioridad {prioridad or 'normal'} en "
                           f"{d('ubicacion') or 'el recinto'}.",
                "enlace": f"{portal_url}/soporte/tickets"}
    if event_type == "ticket.sla_vencido":
        return {"ids": _ids(data, "usuario_id", "asignado_id"), "roles": ["administrador"],
                "asunto": f"SLA vencido en el ticket {d('ticket')} · ExpoNexo", "titulo": "Tiempo de atención vencido",
                "mensaje": f"El ticket {d('ticket')} superó su tiempo de atención y se escaló al nivel "
                           f"{d('nivel') or 'siguiente'}.",
                "enlace": f"{portal_url}/soporte/tickets"}
    if event_type == "dispositivo.caido":
        return {"roles": ["personal", "administrador"],
                "asunto": f"Dispositivo sin reporte: {d('dispositivo')} · ExpoNexo", "titulo": "Dispositivo sin reporte",
                "mensaje": f"El dispositivo {d('dispositivo')} dejó de reportar en {d('ubicacion') or 'el recinto'}; "
                           f"se abrió el ticket {d('ticket')}.",
                "enlace": f"{portal_url}/soporte/dispositivos"}
    return None


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
    aviso = _aviso(event_type, data, portal_url)
    if aviso is None:
        result["canal"] = "ignorado"
        _PROCESSED_EVENT_IDS.add(event_id)
        return result

    # Si la base no responde se lanza: SQS reintenta el mensaje y, tras 5 intentos, va a la DLQ
    contactos = resolve_contacts(aviso.get("ids"), aviso.get("correos"), aviso.get("roles"), http_client)
    html_body, txt_body = render_template(title=aviso["titulo"], message=aviso["mensaje"], portal_link=aviso["enlace"])
    texto_telegram = telegram_text(aviso["titulo"], aviso["mensaje"], aviso["enlace"])
    enviados = {"correo": 0, "telegram": 0}
    for contacto in contactos:
        # Correo y Telegram por separado: si uno falla, el otro sale igual
        try:
            send_brevo_email(contacto["correo"], contacto.get("nombre") or "", aviso["asunto"], html_body, txt_body,
                             http_client)
            enviados["correo"] += 1
        except Exception as exc:
            logger.error("Correo del aviso %s no enviado: %s", event_type, type(exc).__name__)
        if contacto.get("telegram_chat_id"):
            try:
                send_telegram_message(str(contacto["telegram_chat_id"]), texto_telegram, http_client)
                enviados["telegram"] += 1
            except Exception as exc:
                logger.error("Telegram del aviso %s no enviado: %s", event_type, type(exc).__name__)

    if enviados["telegram"]:
        result["canal"] = "correo+telegram"
    elif enviados["correo"]:
        result["canal"] = "correo"
    else:
        result["canal"] = "sin_destinatarios"
    result["enviados"] = enviados
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
