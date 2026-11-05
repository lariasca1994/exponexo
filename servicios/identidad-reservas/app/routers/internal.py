from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ProblemDetailError
from app.models.catalog import StandReservation
from app.models.identity import User
from app.models.tickets_agenda import Ticket
from app.schemas.catalog import (
    InternalReservationResponse,
    MarkReservationPaidRequest,
)
from app.schemas.identity import ContactInfo
from app.schemas.tickets_agenda import (
    ActivateTicketInternalRequest,
    TicketResponse,
)
from app.security.dependencies import require_service_token
from app.services.catalog_service import (
    expire_overdue_reservations,
    mark_reservation_paid,
)
from app.services.outbox_publisher import publish_pending_outbox_events
from app.services.tickets_agenda_service import (
    TICKET_PRICES,
    activate_ticket_internal,
    cancel_ticket_internal,
    refund_reservation_internal,
)


router = APIRouter(prefix="/v1/interno", tags=["Interno"])


@router.get("/salud")
def internal_health(
    service_claims: dict[str, Any] = Depends(require_service_token),
) -> dict[str, str]:
    return {
        "estado": "ok",
        "autenticado_como": str(service_claims.get("sub")),
    }


@router.get("/reservas/{id}", response_model=InternalReservationResponse)
def get_internal_reservation(
    id: str,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> InternalReservationResponse:
    expire_overdue_reservations(db)
    reservation = db.scalar(select(StandReservation).where(StandReservation.id == id))
    if reservation is None:
        raise ProblemDetailError(
            status=404,
            title="Reserva no encontrada",
            detail="No se encontró la reserva solicitada.",
            problem_type="https://exponexo.co/problemas/reserva-no-encontrada",
        )
    return InternalReservationResponse(
        id=reservation.id,
        evento_id=reservation.evento_id,
        stand_id=reservation.stand_id,
        usuario_id=reservation.usuario_id,
        empresa_id=reservation.empresa_id,
        estado=reservation.estado,
        monto=reservation.monto,
        vence_en=reservation.vence_en,
    )


@router.post("/reservas/{id}/pagada", response_model=InternalReservationResponse)
def internal_mark_reservation_paid(
    id: str,
    payload: MarkReservationPaidRequest,
    request: Request,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> InternalReservationResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    reservation = mark_reservation_paid(
        db=db,
        reservation_id=id,
        payment_order_id=payload.orden_pago_id,
        received_event_id=payload.evento_id,
        correlation_id=correlation_id,
    )
    return InternalReservationResponse(
        id=reservation.id,
        evento_id=reservation.evento_id,
        stand_id=reservation.stand_id,
        usuario_id=reservation.usuario_id,
        empresa_id=reservation.empresa_id,
        estado=reservation.estado,
        monto=reservation.monto,
        vence_en=reservation.vence_en,
    )


@router.post("/reservas/{id}/reembolsar", response_model=InternalReservationResponse)
def internal_refund_reservation(
    id: str,
    payload: MarkReservationPaidRequest,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> InternalReservationResponse:
    reservation = refund_reservation_internal(
        db=db,
        reservation_id=id,
        payment_order_id=payload.orden_pago_id,
        received_event_id=payload.evento_id,
    )
    return InternalReservationResponse(
        id=reservation.id,
        evento_id=reservation.evento_id,
        stand_id=reservation.stand_id,
        usuario_id=reservation.usuario_id,
        empresa_id=reservation.empresa_id,
        estado=reservation.estado,
        monto=reservation.monto,
        vence_en=reservation.vence_en,
    )


@router.post("/reservas/vencer")
def internal_expire_reservations(
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    expired = expire_overdue_reservations(db=db)
    return {"cantidad_vencida": expired}


@router.get("/entradas/{id}")
def get_internal_ticket(
    id: str,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ticket = db.scalar(select(Ticket).where(Ticket.id == id))
    if ticket is None:
        raise ProblemDetailError(
            status=404,
            title="Entrada no encontrada",
            detail="No se encontró la entrada solicitada.",
            problem_type="https://exponexo.co/problemas/entrada-no-encontrada",
        )
    return {
        "id": ticket.id,
        "evento_id": ticket.evento_id,
        "usuario_id": ticket.usuario_id,
        "tipo": ticket.tipo,
        "estado": ticket.estado,
        "monto": str(TICKET_PRICES.get(ticket.tipo, TICKET_PRICES["general"])),
    }


@router.post("/entradas/{id}/activar", response_model=TicketResponse)
def internal_activate_ticket(
    id: str,
    payload: ActivateTicketInternalRequest,
    request: Request,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> TicketResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return activate_ticket_internal(
        db=db,
        ticket_id=id,
        payment_order_id=payload.orden_pago_id,
        received_event_id=payload.evento_id,
        correlation_id=correlation_id,
    )


@router.post("/entradas/{id}/cancelar", response_model=TicketResponse)
def internal_cancel_ticket(
    id: str,
    payload: ActivateTicketInternalRequest,
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> TicketResponse:
    return cancel_ticket_internal(
        db=db,
        ticket_id=id,
        payment_order_id=payload.orden_pago_id,
        received_event_id=payload.evento_id,
    )


@router.post("/bandeja/publicar")
def internal_publish_outbox(
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return publish_pending_outbox_events(db=db)


@router.get("/contactos", response_model=list[ContactInfo])
def get_contacts(
    ids: str = "",
    correos: str = "",
    roles: str = "",
    _: dict[str, Any] = Depends(require_service_token),
    db: Session = Depends(get_db),
) -> list[ContactInfo]:
    """Datos de contacto para los avisos, leídos de la base en el momento de enviar.

    Acepta identificadores, correos o roles separados por comas (máximo 50 de cada uno) y solo
    devuelve cuentas activas.
    """
    def lista(valor: str) -> list[str]:
        return [v.strip() for v in valor.split(",") if v.strip()][:50]

    filtros = []
    if lista(ids):
        filtros.append(User.id.in_(lista(ids)))
    if lista(correos):
        filtros.append(User.correo.in_([c.lower() for c in lista(correos)]))
    if lista(roles):
        filtros.append(User.rol.in_(lista(roles)))
    if not filtros:
        return []
    usuarios = db.scalars(select(User).where(User.activo == True, or_(*filtros)))  # noqa: E712
    return [
        ContactInfo(
            usuario_id=u.id,
            correo=u.correo,
            nombre=u.nombre,
            rol=u.rol,
            telegram_chat_id=u.telegram_chat_id,
        )
        for u in usuarios
    ]
