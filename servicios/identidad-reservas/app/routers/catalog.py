from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.catalog import Event, Pavilion, Stand, StandReservation
from app.models.identity import User
from app.models.tickets_agenda import BusinessAppointment, Ticket
from app.schemas.catalog import (
    EventCreateRequest,
    EventResponse,
    EventStandStatusResponse,
    EventUpdateRequest,
    PaginatedEventsResponse,
    PavilionCreateRequest,
    PavilionResponse,
    PavilionUpdateRequest,
    StandCreateRequest,
    StandResponse,
    StandUpdateRequest,
)
from app.security.dependencies import require_roles
from app.services.catalog_service import (
    create_event,
    create_pavilion,
    create_stand,
    get_event_by_slug_or_id,
    list_event_stands_with_status,
    list_public_events,
    update_event,
    update_pavilion,
    update_stand,
)


router = APIRouter(tags=["Catálogo y Administración"])


@router.get("/v1/eventos", response_model=PaginatedEventsResponse)
def get_published_events(
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedEventsResponse:
    total, items = list_public_events(db=db, page=pagina, size=tamano)
    return PaginatedEventsResponse(
        pagina=pagina,
        tamano=tamano,
        total=total,
        items=[EventResponse.model_validate(e) for e in items],
    )


@router.get("/v1/eventos/{slug}", response_model=EventResponse)
def get_event_detail(
    slug: str,
    db: Session = Depends(get_db),
) -> EventResponse:
    event = get_event_by_slug_or_id(db=db, slug_or_id=slug)
    return EventResponse.model_validate(event)


@router.get("/v1/eventos/{id}/stands", response_model=list[EventStandStatusResponse])
def get_event_stands(
    id: str,
    db: Session = Depends(get_db),
) -> list[EventStandStatusResponse]:
    return list_event_stands_with_status(db=db, event_id_or_slug=id)


@router.get("/v1/pabellones", response_model=list[PavilionResponse])
def get_pavilions(db: Session = Depends(get_db)) -> list[PavilionResponse]:
    pavilions = list(db.scalars(select(Pavilion).order_by(Pavilion.nombre.asc())))
    return [PavilionResponse.model_validate(p) for p in pavilions]


@router.post(
    "/v1/admin/eventos",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_event(
    payload: EventCreateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> EventResponse:
    event = create_event(db=db, payload=payload)
    return EventResponse.model_validate(event)


@router.put("/v1/admin/eventos/{id}", response_model=EventResponse)
def admin_update_event(
    id: str,
    payload: EventUpdateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> EventResponse:
    event = update_event(db=db, event_id=id, payload=payload)
    return EventResponse.model_validate(event)


@router.post(
    "/v1/admin/pabellones",
    response_model=PavilionResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_pavilion(
    payload: PavilionCreateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> PavilionResponse:
    pavilion = create_pavilion(db=db, payload=payload)
    return PavilionResponse.model_validate(pavilion)


@router.put("/v1/admin/pabellones/{id}", response_model=PavilionResponse)
def admin_update_pavilion(
    id: str,
    payload: PavilionUpdateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> PavilionResponse:
    pavilion = update_pavilion(db=db, pavilion_id=id, payload=payload)
    return PavilionResponse.model_validate(pavilion)


@router.post(
    "/v1/admin/stands",
    response_model=StandResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_stand(
    payload: StandCreateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> StandResponse:
    stand = create_stand(db=db, payload=payload)
    return StandResponse.model_validate(stand)


@router.put("/v1/admin/stands/{id}", response_model=StandResponse)
def admin_update_stand(
    id: str,
    payload: StandUpdateRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> StandResponse:
    stand = update_stand(db=db, stand_id=id, payload=payload)
    return StandResponse.model_validate(stand)


@router.get("/v1/admin/resumen")
def admin_get_summary(
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    total_events = int(db.scalar(select(func.count()).select_from(Event)) or 0)
    total_stands = int(db.scalar(select(func.count()).select_from(Stand)) or 0)
    occupied_stands = int(
        db.scalar(
            select(func.count())
            .select_from(StandReservation)
            .where(StandReservation.estado.in_(["pendiente_pago", "pagada"]))
        )
        or 0
    )
    paid_stands = int(
        db.scalar(
            select(func.count())
            .select_from(StandReservation)
            .where(StandReservation.estado == "pagada")
        )
        or 0
    )
    total_tickets = int(db.scalar(select(func.count()).select_from(Ticket)) or 0)
    active_or_used_tickets = int(
        db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.estado.in_(["activa", "usada"]))
        )
        or 0
    )
    used_tickets = int(
        db.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.estado == "usada")
        )
        or 0
    )
    accepted_appointments = int(
        db.scalar(
            select(func.count())
            .select_from(BusinessAppointment)
            .where(BusinessAppointment.estado == "aceptada")
        )
        or 0
    )

    occupancy_pct = round((occupied_stands * 100.0 / total_stands), 2) if total_stands > 0 else 0.0

    return {
        "eventos_totales": total_events,
        "stands_totales": total_stands,
        "stands_ocupados": occupied_stands,
        "stands_pagados": paid_stands,
        "ocupacion_stands_porcentaje": occupancy_pct,
        "entradas_emitidas": total_tickets,
        "entradas_activas_o_usadas": active_or_used_tickets,
        "entradas_validadas_puerta": used_tickets,
        "citas_negocios_aceptadas": accepted_appointments,
    }

