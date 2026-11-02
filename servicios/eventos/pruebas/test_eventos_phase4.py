import json
from typing import Any

from avisos.funcion import handler as avisos_handler, reset_processed_events
from repartidor.funcion import handler as repartidor_handler
from repartidor.rutas import resolve_route


def _build_sqs_record(message_id: str, envelope: dict[str, Any], sns_wrapped: bool = False) -> dict[str, Any]:
    body_json = json.dumps(envelope)
    if sns_wrapped:
        body_json = json.dumps({"Type": "Notification", "Message": body_json})
    return {
        "messageId": message_id,
        "body": body_json,
    }


def test_repartidor_resolves_pago_aprobado_for_reserva_and_entrada() -> None:
    urls = {"identidad-reservas": "http://localhost:8001"}

    env_reserva = {
        "id": "evt-001",
        "tipo": "pago.aprobado",
        "version": 1,
        "ocurrido_en": "2026-11-02T18:00:00Z",
        "origen": "pagos",
        "correlacion_id": "corr-001",
        "datos": {
            "orden": "ord-123",
            "referencia": "res-456",
            "origen": "reserva_stand",
            "monto": 2500000.0,
            "factura": "EXN-000001",
        },
    }
    target_res = resolve_route(env_reserva, base_urls=urls)
    assert target_res is not None
    assert target_res.url == "http://localhost:8001/v1/interno/reservas/res-456/pagada"
    assert target_res.payload == {"orden_pago_id": "ord-123", "evento_id": "evt-001"}

    env_entrada = {
        **env_reserva,
        "id": "evt-002",
        "datos": {
            "orden": "ord-999",
            "referencia": "ent-777",
            "origen": "entrada",
            "monto": 120000.0,
            "factura": "EXN-000002",
        },
    }
    target_ent = resolve_route(env_entrada, base_urls=urls)
    assert target_ent is not None
    assert target_ent.url == "http://localhost:8001/v1/interno/entradas/ent-777/activar"
    assert target_ent.payload == {"orden_pago_id": "ord-999", "evento_id": "evt-002"}


def test_repartidor_partial_batch_failure_reports_only_failed_record() -> None:
    dispatched_ids: list[str] = []

    def fake_dispatcher(envelope: dict[str, Any]) -> None:
        if envelope.get("id") == "evt-malo":
            raise RuntimeError("Servicio destino temporalmente no disponible")
        dispatched_ids.append(str(envelope.get("id")))

    sqs_event = {
        "Records": [
            _build_sqs_record(
                "msg-1",
                {
                    "id": "evt-bueno-1",
                    "tipo": "pago.aprobado",
                    "datos": {"orden": "o1", "referencia": "r1", "origen": "reserva_stand"},
                },
                sns_wrapped=True,
            ),
            _build_sqs_record(
                "msg-2",
                {
                    "id": "evt-malo",
                    "tipo": "pago.aprobado",
                    "datos": {"orden": "o2", "referencia": "r2", "origen": "reserva_stand"},
                },
            ),
            _build_sqs_record(
                "msg-3",
                {
                    "id": "evt-bueno-2",
                    "tipo": "pago.reembolsado",
                    "datos": {"orden": "o3", "referencia": "r3", "origen": "reserva_stand"},
                },
            ),
        ]
    }

    response = repartidor_handler(sqs_event, dispatcher=fake_dispatcher)
    assert response == {"batchItemFailures": [{"itemIdentifier": "msg-2"}]}
    assert dispatched_ids == ["evt-bueno-1", "evt-bueno-2"]


def test_avisos_idempotency_and_sensitive_data_guard() -> None:
    reset_processed_events()

    good_event = {
        "id": "evt-aviso-1",
        "tipo": "cuenta.creada",
        "version": 1,
        "origen": "identidad-reservas",
        "datos": {
            "usuario": "u-1",
            "correo": "ana@empresa.co",
            "nombre": "Ana Gómez",
        },
    }
    sensitive_event = {
        "id": "evt-aviso-sensible",
        "tipo": "cuenta.creada",
        "version": 1,
        "origen": "identidad-reservas",
        "datos": {
            "usuario": "u-2",
            "correo": "ana@empresa.co",
            "contrasena": "ClaveEnTextoPlano123",
        },
    }

    sqs_batch = {
        "Records": [
            _build_sqs_record("m-ok-1", good_event),
            _build_sqs_record("m-ok-dup", good_event),
            _build_sqs_record("m-bad-sensitive", sensitive_event),
        ]
    }

    result = avisos_handler(sqs_batch)
    assert result == {"batchItemFailures": [{"itemIdentifier": "m-bad-sensitive"}]}
