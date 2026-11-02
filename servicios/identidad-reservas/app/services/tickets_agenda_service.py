from datetime import datetime, timezone
from decimal import Decimal
import json
import uuid

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from app.errors import ProblemDetailError
from app.models.catalog import Event, Pavilion, StandReservation
from app.models.identity import Company, OutboxEvent, ProcessedEvent, User
from app.models.tickets_agenda import (
    AvailabilitySlot,
    BusinessAppointment,
    MeetingRoom,
    Ticket,
)
from app.schemas.tickets_agenda import (
    AppointmentResponse,
    AvailabilityResponse,
    CreateMeetingRoomRequest,
    FreeSlotResponse,
    MeetingRoomResponse,
    ProposeAppointmentRequest,
    PurchaseTicketRequest,
    TicketResponse,
    UpdateAvailabilityRequest,
    ValidateTicketQrRequest,
    ValidateTicketQrResponse,
)
from app.security.ticket_qr import sign_ticket_qr, verify_ticket_qr


TICKET_PRICES: dict[str, Decimal] = {
    "general": Decimal("45000.00"),
    "negocios": Decimal("120000.00"),
    "prensa": Decimal("25000.00"),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _ticket_to_response(db: Session, ticket: Ticket) -> TicketResponse:
    event = db.scalar(select(Event).where(Event.id == ticket.evento_id))
    return TicketResponse(
        id=ticket.id,
        evento_id=ticket.evento_id,
        evento_nombre=event.nombre if event else None,
        usuario_id=ticket.usuario_id,
        tipo=ticket.tipo,
        estado=ticket.estado,
        precio_sugerido=TICKET_PRICES.get(ticket.tipo, Decimal("45000.00")),
        orden_pago_id=ticket.orden_pago_id,
        codigo_qr=ticket.codigo_qr,
        usada_en=ticket.usada_en,
        usada_en_dispositivo=ticket.usada_en_dispositivo,
        creada_en=ticket.creada_en,
    )


def purchase_ticket(
    db: Session,
    event_id: str,
    user: User,
    payload: PurchaseTicketRequest,
) -> TicketResponse:
    event = db.scalar(select(Event).where(Event.id == event_id))
    if event is None or event.estado in {"cerrado", "borrador"}:
        raise ProblemDetailError(
            status=404,
            title="Evento no disponible",
            detail="El evento solicitado no existe o no admite compra de entradas.",
            problem_type="https://exponexo.co/problemas/evento-no-disponible",
        )

    ticket = Ticket(
        id=str(uuid.uuid4()),
        evento_id=event.id,
        usuario_id=user.id,
        tipo=payload.tipo,
        estado="pendiente_pago",
        creada_en=utc_now(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(db, ticket)


def list_user_tickets(db: Session, user_id: str) -> list[TicketResponse]:
    tickets = list(
        db.scalars(
            select(Ticket)
            .where(Ticket.usuario_id == user_id)
            .order_by(Ticket.creada_en.desc())
        ).all()
    )
    return [_ticket_to_response(db, t) for t in tickets]


def activate_ticket_internal(
    db: Session,
    ticket_id: str,
    payment_order_id: str,
    received_event_id: str | None = None,
    correlation_id: str | None = None,
) -> TicketResponse:
    dedup_id = received_event_id or f"pago-entrada-{payment_order_id}"
    already = db.scalar(select(ProcessedEvent).where(ProcessedEvent.evento_id == dedup_id))
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if ticket is None:
        raise ProblemDetailError(
            status=404,
            title="Entrada no encontrada",
            detail="No existe la entrada indicada.",
            problem_type="https://exponexo.co/problemas/entrada-no-encontrada",
        )

    if already is not None or ticket.estado in {"activa", "usada"}:
        return _ticket_to_response(db, ticket)

    qr_code = sign_ticket_qr(
        ticket_id=ticket.id,
        event_id=ticket.evento_id,
        user_id=ticket.usuario_id,
        ticket_type=ticket.tipo,
    )
    ticket.estado = "activa"
    ticket.orden_pago_id = payment_order_id
    ticket.codigo_qr = qr_code

    db.add(
        ProcessedEvent(
            evento_id=dedup_id,
            procesado_en=utc_now(),
        )
    )
    user = db.scalar(select(User).where(User.id == ticket.usuario_id))
    db.add(
        OutboxEvent(
            id=str(uuid.uuid4()),
            tipo="entrada.activada",
            carga=json.dumps(
                {
                    "entrada": ticket.id,
                    "evento": ticket.evento_id,
                    "usuario": ticket.usuario_id,
                    "correo": user.correo if user else "visitante@exponexo.co",
                }
            ),
            correlacion_id=correlation_id,
            creado_en=utc_now(),
            intentos=0,
        )
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(db, ticket)


def cancel_ticket_internal(
    db: Session,
    ticket_id: str,
    payment_order_id: str,
    received_event_id: str | None = None,
) -> TicketResponse:
    dedup_id = received_event_id or f"reembolso-entrada-{payment_order_id}"
    already = db.scalar(select(ProcessedEvent).where(ProcessedEvent.evento_id == dedup_id))
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if ticket is None:
        raise ProblemDetailError(
            status=404,
            title="Entrada no encontrada",
            detail="No existe la entrada indicada.",
            problem_type="https://exponexo.co/problemas/entrada-no-encontrada",
        )
    if already is not None or ticket.estado == "cancelada":
        return _ticket_to_response(db, ticket)

    ticket.estado = "cancelada"
    ticket.codigo_qr = None
    db.add(
        ProcessedEvent(
            evento_id=dedup_id,
            procesado_en=utc_now(),
        )
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_to_response(db, ticket)


def refund_reservation_internal(
    db: Session,
    reservation_id: str,
    payment_order_id: str,
    received_event_id: str | None = None,
) -> StandReservation:
    dedup_id = received_event_id or f"reembolso-reserva-{payment_order_id}"
    already = db.scalar(select(ProcessedEvent).where(ProcessedEvent.evento_id == dedup_id))
    reservation = db.scalar(select(StandReservation).where(StandReservation.id == reservation_id))
    if reservation is None:
        raise ProblemDetailError(
            status=404,
            title="Reserva no encontrada",
            detail="No se encontró la reserva para reembolsar.",
            problem_type="https://exponexo.co/problemas/reserva-no-encontrada",
        )
    if already is not None or reservation.estado == "cancelada":
        return reservation

    reservation.estado = "cancelada"
    db.add(
        ProcessedEvent(
            evento_id=dedup_id,
            procesado_en=utc_now(),
        )
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def validate_ticket_qr(
    db: Session,
    payload: ValidateTicketQrRequest,
) -> ValidateTicketQrResponse:
    qr_claims = verify_ticket_qr(payload.codigo_qr)
    ticket_id = str(qr_claims.get("entrada_id", ""))
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if ticket is None or ticket.codigo_qr != payload.codigo_qr:
        raise ProblemDetailError(
            status=400,
            title="Entrada inválida",
            detail="El código QR no corresponde a una entrada activa registrada.",
            problem_type="https://exponexo.co/problemas/qr-entrada-no-coincide",
        )

    if ticket.estado == "usada":
        raise ProblemDetailError(
            status=409,
            title="Entrada ya utilizada",
            detail=f"La entrada ya fue utilizada previamente en el dispositivo {ticket.usada_en_dispositivo}.",
            problem_type="https://exponexo.co/problemas/entrada-ya-usada",
        )

    if ticket.estado != "activa":
        raise ProblemDetailError(
            status=409,
            title="Entrada no activa",
            detail=f"La entrada se encuentra en estado '{ticket.estado}' y no permite el ingreso.",
            problem_type="https://exponexo.co/problemas/entrada-no-activa",
        )

    now = utc_now()
    ticket.estado = "usada"
    ticket.usada_en = now
    ticket.usada_en_dispositivo = payload.dispositivo_id
    db.commit()
    db.refresh(ticket)

    return ValidateTicketQrResponse(
        valida=True,
        entrada_id=ticket.id,
        evento_id=ticket.evento_id,
        usuario_id=ticket.usuario_id,
        tipo=ticket.tipo,
        estado=ticket.estado,
        usada_en=now,
        usada_en_dispositivo=payload.dispositivo_id,
    )


def create_meeting_room(
    db: Session,
    pavilion_id: str,
    payload: CreateMeetingRoomRequest,
) -> MeetingRoomResponse:
    pavilion = db.scalar(select(Pavilion).where(Pavilion.id == pavilion_id))
    if pavilion is None:
        raise ProblemDetailError(
            status=404,
            title="Pabellón no encontrado",
            detail="El pabellón indicado no existe.",
            problem_type="https://exponexo.co/problemas/pabellon-no-encontrado",
        )

    existing = db.scalar(
        select(MeetingRoom).where(
            and_(
                MeetingRoom.pabellon_id == pavilion_id,
                MeetingRoom.codigo == payload.codigo,
            )
        )
    )
    if existing is not None:
        raise ProblemDetailError(
            status=409,
            title="Sala duplicada",
            detail="Ya existe una sala con ese código en el pabellón.",
            problem_type="https://exponexo.co/problemas/sala-duplicada",
        )

    room = MeetingRoom(
        id=str(uuid.uuid4()),
        pabellon_id=pavilion_id,
        codigo=payload.codigo,
        capacidad=payload.capacidad,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return MeetingRoomResponse(
        id=room.id,
        pabellon_id=room.pabellon_id,
        codigo=room.codigo,
        capacidad=room.capacidad,
    )


def update_user_availability(
    db: Session,
    event_id: str,
    user: User,
    payload: UpdateAvailabilityRequest,
) -> list[AvailabilityResponse]:
    event = db.scalar(select(Event).where(Event.id == event_id))
    if event is None:
        raise ProblemDetailError(
            status=404,
            title="Evento no encontrado",
            detail="El evento indicado no existe.",
            problem_type="https://exponexo.co/problemas/evento-no-encontrado",
        )

    for block in payload.bloques:
        if _as_utc(block.hasta) <= _as_utc(block.desde):
            raise ProblemDetailError(
                status=400,
                title="Bloque de horario inválido",
                detail="La fecha/hora final de cada bloque debe ser posterior a la inicial.",
                problem_type="https://exponexo.co/problemas/disponibilidad-rango-invalido",
            )

    db.execute(
        delete(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.evento_id == event_id,
                AvailabilitySlot.usuario_id == user.id,
            )
        )
    )

    created_slots: list[AvailabilitySlot] = []
    for block in payload.bloques:
        slot = AvailabilitySlot(
            id=str(uuid.uuid4()),
            usuario_id=user.id,
            evento_id=event_id,
            desde=_as_utc(block.desde),
            hasta=_as_utc(block.hasta),
        )
        db.add(slot)
        created_slots.append(slot)

    db.commit()
    return [
        AvailabilityResponse(
            id=s.id,
            usuario_id=s.usuario_id,
            evento_id=s.evento_id,
            desde=s.desde,
            hasta=s.hasta,
        )
        for s in created_slots
    ]


def get_exhibitor_free_slots(
    db: Session,
    event_id: str,
    exhibitor_id: str,
) -> list[FreeSlotResponse]:
    exhibitor = db.scalar(select(User).where(User.id == exhibitor_id))
    if exhibitor is None:
        raise ProblemDetailError(
            status=404,
            title="Expositor no encontrado",
            detail="No se encontró el usuario expositor indicado.",
            problem_type="https://exponexo.co/problemas/expositor-no-encontrado",
        )

    company_name: str | None = None

    slots = list(
        db.scalars(
            select(AvailabilitySlot)
            .where(
                and_(
                    AvailabilitySlot.evento_id == event_id,
                    AvailabilitySlot.usuario_id == exhibitor_id,
                )
            )
            .order_by(AvailabilitySlot.desde.asc())
        ).all()
    )

    accepted_appointments = list(
        db.scalars(
            select(BusinessAppointment)
            .where(
                and_(
                    BusinessAppointment.evento_id == event_id,
                    BusinessAppointment.estado == "aceptada",
                    or_(
                        BusinessAppointment.solicitante_id == exhibitor_id,
                        BusinessAppointment.anfitrion_id == exhibitor_id,
                    ),
                )
            )
            .order_by(BusinessAppointment.inicio.asc())
        ).all()
    )

    free_segments: list[FreeSlotResponse] = []
    for slot in slots:
        segments: list[tuple[datetime, datetime]] = [(_as_utc(slot.desde), _as_utc(slot.hasta))]
        for appt in accepted_appointments:
            busy_start = _as_utc(appt.inicio)
            busy_end = _as_utc(appt.fin)
            next_segments: list[tuple[datetime, datetime]] = []
            for seg_start, seg_end in segments:
                if busy_end <= seg_start or busy_start >= seg_end:
                    next_segments.append((seg_start, seg_end))
                else:
                    if busy_start > seg_start:
                        next_segments.append((seg_start, busy_start))
                    if busy_end < seg_end:
                        next_segments.append((busy_end, seg_end))
            segments = next_segments

        for seg_start, seg_end in segments:
            if seg_end > seg_start:
                free_segments.append(
                    FreeSlotResponse(
                        expositor_id=exhibitor.id,
                        expositor_nombre=exhibitor.nombre,
                        empresa_nombre=company_name,
                        desde=seg_start,
                        hasta=seg_end,
                    )
                )

    return free_segments


def _appointment_to_response(db: Session, appt: BusinessAppointment) -> AppointmentResponse:
    solicitante = db.scalar(select(User).where(User.id == appt.solicitante_id))
    anfitrion = db.scalar(select(User).where(User.id == appt.anfitrion_id))
    room = db.scalar(select(MeetingRoom).where(MeetingRoom.id == appt.sala_id)) if appt.sala_id else None
    return AppointmentResponse(
        id=appt.id,
        evento_id=appt.evento_id,
        solicitante_id=appt.solicitante_id,
        solicitante_nombre=solicitante.nombre if solicitante else None,
        anfitrion_id=appt.anfitrion_id,
        anfitrion_nombre=anfitrion.nombre if anfitrion else None,
        sala_id=appt.sala_id,
        sala_codigo=room.codigo if room else None,
        inicio=appt.inicio,
        fin=appt.fin,
        estado=appt.estado,
        mensaje=appt.mensaje,
        creada_en=appt.creada_en,
    )


def propose_appointment(
    db: Session,
    requester: User,
    payload: ProposeAppointmentRequest,
) -> AppointmentResponse:
    if requester.id == payload.anfitrion_id:
        raise ProblemDetailError(
            status=400,
            title="Participantes inválidos",
            detail="No puedes proponerte una cita de negocios a ti mismo.",
            problem_type="https://exponexo.co/problemas/cita-mismo-participante",
        )

    start_utc = _as_utc(payload.inicio)
    end_utc = _as_utc(payload.fin)
    if end_utc <= start_utc:
        raise ProblemDetailError(
            status=400,
            title="Horario de cita inválido",
            detail="La hora de finalización debe ser posterior a la hora de inicio.",
            problem_type="https://exponexo.co/problemas/cita-rango-invalido",
        )

    host = db.scalar(select(User).where(User.id == payload.anfitrion_id))
    if host is None:
        raise ProblemDetailError(
            status=404,
            title="Anfitrión no encontrado",
            detail="La persona con quien solicitas la cita no existe.",
            problem_type="https://exponexo.co/problemas/anfitrion-no-encontrado",
        )

    appt = BusinessAppointment(
        id=str(uuid.uuid4()),
        evento_id=payload.evento_id,
        solicitante_id=requester.id,
        anfitrion_id=payload.anfitrion_id,
        inicio=start_utc,
        fin=end_utc,
        estado="propuesta",
        mensaje=payload.mensaje,
        creada_en=utc_now(),
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return _appointment_to_response(db, appt)


def respond_appointment(
    db: Session,
    appointment_id: str,
    host: User,
    decision: str,
    correlation_id: str | None = None,
) -> AppointmentResponse:
    appt = db.scalar(select(BusinessAppointment).where(BusinessAppointment.id == appointment_id))
    if appt is None:
        raise ProblemDetailError(
            status=404,
            title="Cita no encontrada",
            detail="No existe la cita solicitada.",
            problem_type="https://exponexo.co/problemas/cita-no-encontrada",
        )

    if appt.anfitrion_id != host.id and host.rol != "administrador":
        raise ProblemDetailError(
            status=403,
            title="Sin permiso sobre la cita",
            detail="Solo la persona anfitriona puede aceptar o rechazar esta cita.",
            problem_type="https://exponexo.co/problemas/cita-sin-permiso",
        )

    if appt.estado != "propuesta":
        raise ProblemDetailError(
            status=409,
            title="Estado de cita no modificable",
            detail=f"La cita ya se encuentra en estado '{appt.estado}'.",
            problem_type="https://exponexo.co/problemas/cita-estado-invalido",
        )

    if decision == "rechazar":
        appt.estado = "rechazada"
        db.commit()
        db.refresh(appt)
        return _appointment_to_response(db, appt)

    # Aceptar cita: comprobar traslape de ambos participantes y buscar sala libre
    start_utc = _as_utc(appt.inicio)
    end_utc = _as_utc(appt.fin)

    existing_accepted = list(
        db.scalars(
            select(BusinessAppointment).where(
                and_(
                    BusinessAppointment.evento_id == appt.evento_id,
                    BusinessAppointment.estado == "aceptada",
                    BusinessAppointment.id != appt.id,
                )
            )
        ).all()
    )

    participants = {appt.solicitante_id, appt.anfitrion_id}
    occupied_room_ids: set[str] = set()

    for other in existing_accepted:
        other_start = _as_utc(other.inicio)
        other_end = _as_utc(other.fin)
        if other_start < end_utc and other_end > start_utc:
            if other.solicitante_id in participants or other.anfitrion_id in participants:
                raise ProblemDetailError(
                    status=409,
                    title="Cruces de agenda",
                    detail="Uno de los participantes ya tiene otra cita aceptada que se cruza con este horario.",
                    problem_type="https://exponexo.co/problemas/cita-cruce-participante",
                )
            if other.sala_id:
                occupied_room_ids.add(other.sala_id)

    event_rooms = list(
        db.scalars(
            select(MeetingRoom)
            .join(Pavilion, Pavilion.id == MeetingRoom.pabellon_id)
            .order_by(MeetingRoom.codigo.asc())
        ).all()
    )

    free_room = next((r for r in event_rooms if r.id not in occupied_room_ids), None)
    if free_room is None:
        raise ProblemDetailError(
            status=409,
            title="Sin salas disponibles",
            detail="No hay salas de negocios libres en el evento para el horario seleccionado.",
            problem_type="https://exponexo.co/problemas/cita-sin-sala-libre",
        )

    appt.sala_id = free_room.id
    appt.estado = "aceptada"

    solicitante = db.scalar(select(User).where(User.id == appt.solicitante_id))
    anfitrion = db.scalar(select(User).where(User.id == appt.anfitrion_id))
    db.add(
        OutboxEvent(
            id=str(uuid.uuid4()),
            tipo="cita.aceptada",
            carga=json.dumps(
                {
                    "cita": appt.id,
                    "evento": appt.evento_id,
                    "sala": free_room.codigo,
                    "inicio": start_utc.isoformat(),
                    "fin": end_utc.isoformat(),
                    "participantes": [
                        solicitante.correo if solicitante else appt.solicitante_id,
                        anfitrion.correo if anfitrion else appt.anfitrion_id,
                    ],
                }
            ),
            correlacion_id=correlation_id,
            creado_en=utc_now(),
            intentos=0,
        )
    )
    db.commit()
    db.refresh(appt)
    return _appointment_to_response(db, appt)


def list_user_appointments(db: Session, user_id: str) -> list[AppointmentResponse]:
    appts = list(
        db.scalars(
            select(BusinessAppointment)
            .where(
                or_(
                    BusinessAppointment.solicitante_id == user_id,
                    BusinessAppointment.anfitrion_id == user_id,
                )
            )
            .order_by(BusinessAppointment.inicio.asc())
        ).all()
    )
    return [_appointment_to_response(db, a) for a in appts]
