from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.identity import Company, User
from app.models.tickets_agenda import AvailabilitySlot
from app.schemas.tickets_agenda import (
    AppointmentResponse,
    AvailabilityResponse,
    CreateMeetingRoomRequest,
    FreeSlotResponse,
    MeetingRoomResponse,
    ProposeAppointmentRequest,
    PurchaseTicketRequest,
    RespondAppointmentRequest,
    TicketResponse,
    UpdateAvailabilityRequest,
    ValidateTicketQrRequest,
    ValidateTicketQrResponse,
)
from app.security.dependencies import get_current_user, require_roles
from app.services.tickets_agenda_service import (
    create_meeting_room,
    get_exhibitor_free_slots,
    list_user_appointments,
    list_user_tickets,
    propose_appointment,
    purchase_ticket,
    respond_appointment,
    update_user_availability,
    validate_ticket_qr,
)


router = APIRouter(prefix="/v1", tags=["Entradas y agenda"])


@router.post(
    "/eventos/{id}/entradas",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def buy_event_ticket(
    id: str,
    payload: PurchaseTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResponse:
    return purchase_ticket(db=db, event_id=id, user=current_user, payload=payload)


@router.get("/mis-entradas", response_model=list[TicketResponse])
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    return list_user_tickets(db=db, user_id=current_user.id)


@router.post("/entradas/validar-qr", response_model=ValidateTicketQrResponse)
def validate_entry_qr(
    payload: ValidateTicketQrRequest,
    _: User = Depends(require_roles("personal", "administrador")),
    db: Session = Depends(get_db),
) -> ValidateTicketQrResponse:
    return validate_ticket_qr(db=db, payload=payload)


@router.post(
    "/pabellones/{id}/salas",
    response_model=MeetingRoomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pavilion_room(
    id: str,
    payload: CreateMeetingRoomRequest,
    _: User = Depends(require_roles("administrador")),
    db: Session = Depends(get_db),
) -> MeetingRoomResponse:
    return create_meeting_room(db=db, pavilion_id=id, payload=payload)


@router.put("/eventos/{id}/mi-disponibilidad", response_model=list[AvailabilityResponse])
def put_my_availability(
    id: str,
    payload: UpdateAvailabilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AvailabilityResponse]:
    return update_user_availability(db=db, event_id=id, user=current_user, payload=payload)


@router.get("/eventos/{id}/expositores")
def list_event_exhibitors_with_availability(
    id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, str | None]]:
    user_ids = list(
        set(
            db.scalars(
                select(AvailabilitySlot.usuario_id).where(AvailabilitySlot.evento_id == id)
            ).all()
        )
    )
    if not user_ids:
        expositores = list(
            db.scalars(select(User).where(User.rol.in_(["expositor", "administrador"]))).all()
        )
    else:
        expositores = list(db.scalars(select(User).where(User.id.in_(user_ids))).all())

    result: list[dict[str, str | None]] = []
    for u in expositores:
        result.append(
            {
                "id": u.id,
                "nombre_completo": u.nombre,
                "empresa_nombre": None,
            }
        )
    return result


@router.get("/eventos/{id}/expositores/{exp}/huecos", response_model=list[FreeSlotResponse])
def get_exhibitor_free_gaps(
    id: str,
    exp: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FreeSlotResponse]:
    return get_exhibitor_free_slots(db=db, event_id=id, exhibitor_id=exp)


@router.post("/citas", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_business_appointment(
    payload: ProposeAppointmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    return propose_appointment(db=db, requester=current_user, payload=payload)


@router.post("/citas/{id}/responder", response_model=AppointmentResponse)
def reply_to_business_appointment(
    id: str,
    payload: RespondAppointmentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return respond_appointment(
        db=db,
        appointment_id=id,
        host=current_user,
        decision=payload.decision,
        correlation_id=correlation_id,
    )


@router.get("/mis-citas", response_model=list[AppointmentResponse])
def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    return list_user_appointments(db=db, user_id=current_user.id)
