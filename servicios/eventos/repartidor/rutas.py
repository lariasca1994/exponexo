import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InternalRouteTarget:
    service_name: str
    method: str
    url: str
    payload: dict[str, Any]


def resolve_route(envelope: dict[str, Any], base_urls: dict[str, str] | None = None) -> InternalRouteTarget | None:
    """
    Tabla 'tipo de evento -> servicio y ruta interna'.
    Devuelve None si el evento no requiere acción del repartidor (por ejemplo, solo avisos).
    """
    urls = base_urls or {
        "identidad-reservas": os.getenv("IDENTIDAD_URL", "http://localhost:8001").rstrip("/"),
        "pagos": os.getenv("PAGOS_URL", "http://localhost:8002").rstrip("/"),
        "mesa-ayuda": os.getenv("MESA_AYUDA_URL", "http://localhost:8003").rstrip("/"),
    }

    event_id = str(envelope.get("id", ""))
    event_type = str(envelope.get("tipo", ""))
    data = envelope.get("datos") or {}

    if event_type == "pago.aprobado":
        origin = str(data.get("origen", "reserva_stand"))
        reference_id = str(data.get("referencia", ""))
        order_id = str(data.get("orden", ""))
        if not reference_id or not order_id:
            raise ValueError("El evento pago.aprobado no incluye referencia u orden")

        if origin == "entrada":
            return InternalRouteTarget(
                service_name="identidad-reservas",
                method="POST",
                url=f"{urls['identidad-reservas']}/v1/interno/entradas/{reference_id}/activar",
                payload={
                    "orden_pago_id": order_id,
                    "evento_id": event_id,
                },
            )

        return InternalRouteTarget(
            service_name="identidad-reservas",
            method="POST",
            url=f"{urls['identidad-reservas']}/v1/interno/reservas/{reference_id}/pagada",
            payload={
                "orden_pago_id": order_id,
                "evento_id": event_id,
            },
        )

    if event_type == "pago.reembolsado":
        origin = str(data.get("origen", "reserva_stand"))
        reference_id = str(data.get("referencia", ""))
        order_id = str(data.get("orden", ""))
        if not reference_id or not order_id:
            raise ValueError("El evento pago.reembolsado no incluye referencia u orden")

        if origin == "entrada":
            return InternalRouteTarget(
                service_name="identidad-reservas",
                method="POST",
                url=f"{urls['identidad-reservas']}/v1/interno/entradas/{reference_id}/cancelar",
                payload={
                    "orden_pago_id": order_id,
                    "evento_id": event_id,
                },
            )

        return InternalRouteTarget(
            service_name="identidad-reservas",
            method="POST",
            url=f"{urls['identidad-reservas']}/v1/interno/reservas/{reference_id}/reembolsar",
            payload={
                "orden_pago_id": order_id,
                "evento_id": event_id,
            },
        )

    return None
