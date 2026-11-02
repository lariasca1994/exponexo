from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import uuid

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ProblemDetailError
from app.models.catalog import Event, Pavilion, Stand, StandReservation
from app.models.identity import AuditLog, Company, OutboxEvent, ProcessedEvent, User
from app.schemas.catalog import (
    CompanyCreateRequest,
    EventCreateRequest,
    EventStandStatusResponse,
    EventUpdateRequest,
    PavilionCreateRequest,
    PavilionUpdateRequest,
    ReservationCreateRequest,
    StandCreateRequest,
    StandUpdateRequest,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def upsert_exhibitor_company(
    db: Session,
    user: User,
    payload: CompanyCreateRequest,
) -> Company:
    normalized_nit = payload.nit.strip()
    existing_by_nit = db.scalar(select(Company).where(Company.nit == normalized_nit))
    if existing_by_nit and existing_by_nit.id != user.empresa_id:
        raise ProblemDetailError(
            status=409,
            title="NIT ya registrado",
            detail="Ya existe una empresa registrada con este NIT.",
            problem_type="https://exponexo.co/problemas/nit-duplicado",
        )

    if user.empresa_id:
        company = db.scalar(select(Company).where(Company.id == user.empresa_id))
        if company:
            company.nit = normalized_nit
            company.razon_social = payload.razon_social.strip()
            company.sector = payload.sector.strip()
            company.sitio_web = payload.sitio_web
            company.logo_url = payload.logo_url
            db.commit()
            db.refresh(company)
            return company

    company = Company(
        nit=normalized_nit,
        razon_social=payload.razon_social.strip(),
        sector=payload.sector.strip(),
        sitio_web=payload.sitio_web,
        logo_url=payload.logo_url,
    )
    db.add(company)
    db.flush()
    user.empresa_id = company.id
    db.commit()
    db.refresh(company)
    return company


def create_event(db: Session, payload: EventCreateRequest) -> Event:
    if _ensure_utc(payload.fin) <= _ensure_utc(payload.inicio):
        raise ProblemDetailError(
            status=422,
            title="Fechas de evento inválidas",
            detail="La fecha de fin debe ser posterior a la fecha de inicio.",
            problem_type="https://exponexo.co/problemas/fechas-invalidas",
        )

    existing = db.scalar(select(Event).where(Event.slug == payload.slug))
    if existing is not None:
        raise ProblemDetailError(
            status=409,
            title="Slug de evento duplicado",
            detail="Ya existe un evento con ese identificador URL (slug).",
            problem_type="https://exponexo.co/problemas/slug-duplicado",
        )

    event = Event(
        nombre=payload.nombre.strip(),
        slug=payload.slug.strip(),
        descripcion=payload.descripcion.strip(),
        inicio=_ensure_utc(payload.inicio),
        fin=_ensure_utc(payload.fin),
        estado=payload.estado,
        precio_entrada=payload.precio_entrada,
        aforo=payload.aforo,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event_id: str, payload: EventUpdateRequest) -> Event:
    event = db.scalar(select(Event).where(Event.id == event_id))
    if event is None:
        raise ProblemDetailError(
            status=404,
            title="Evento no encontrado",
            detail="El evento indicado no existe.",
            problem_type="https://exponexo.co/problemas/evento-no-encontrado",
        )

    if payload.nombre is not None:
        event.nombre = payload.nombre.strip()
    if payload.descripcion is not None:
        event.descripcion = payload.descripcion.strip()
    if payload.inicio is not None:
        event.inicio = _ensure_utc(payload.inicio)
    if payload.fin is not None:
        event.fin = _ensure_utc(payload.fin)
    if payload.estado is not None:
        event.estado = payload.estado
    if payload.precio_entrada is not None:
        event.precio_entrada = payload.precio_entrada
    if payload.aforo is not None:
        event.aforo = payload.aforo

    if _ensure_utc(event.fin) <= _ensure_utc(event.inicio):
        raise ProblemDetailError(
            status=422,
            title="Fechas de evento inválidas",
            detail="La fecha de fin debe ser posterior a la fecha de inicio.",
            problem_type="https://exponexo.co/problemas/fechas-invalidas",
        )

    db.commit()
    db.refresh(event)
    return event


def list_public_events(
    db: Session,
    page: int = 1,
    size: int = 20,
) -> tuple[int, list[Event]]:
    # Automatically expire overdue reservations before listing
    expire_overdue_reservations(db)
    condition = Event.estado.in_(["publicado", "en_curso"])
    total = db.scalar(select(func.count(Event.id)).where(condition)) or 0
    items = list(
        db.scalars(
            select(Event)
            .where(condition)
            .order_by(Event.inicio.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
    )
    return total, items


def get_event_by_slug_or_id(db: Session, slug_or_id: str) -> Event:
    event = db.scalar(
        select(Event).where(or_(Event.slug == slug_or_id, Event.id == slug_or_id))
    )
    if event is None:
        raise ProblemDetailError(
            status=404,
            title="Evento no encontrado",
            detail="No se encontró el evento solicitado.",
            problem_type="https://exponexo.co/problemas/evento-no-encontrado",
        )
    return event


def create_pavilion(db: Session, payload: PavilionCreateRequest) -> Pavilion:
    pavilion = Pavilion(
        nombre=payload.nombre.strip(),
        capacidad_stands=payload.capacidad_stands,
        plano_url=payload.plano_url,
    )
    db.add(pavilion)
    db.commit()
    db.refresh(pavilion)
    return pavilion


def update_pavilion(
    db: Session,
    pavilion_id: str,
    payload: PavilionUpdateRequest,
) -> Pavilion:
    pavilion = db.scalar(select(Pavilion).where(Pavilion.id == pavilion_id))
    if pavilion is None:
        raise ProblemDetailError(
            status=404,
            title="Pabellón no encontrado",
            detail="El pabellón indicado no existe.",
            problem_type="https://exponexo.co/problemas/pabellon-no-encontrado",
        )
    if payload.nombre is not None:
        pavilion.nombre = payload.nombre.strip()
    if payload.capacidad_stands is not None:
        pavilion.capacidad_stands = payload.capacidad_stands
    if payload.plano_url is not None:
        pavilion.plano_url = payload.plano_url

    db.commit()
    db.refresh(pavilion)
    return pavilion


def create_stand(db: Session, payload: StandCreateRequest) -> Stand:
    pavilion = db.scalar(select(Pavilion).where(Pavilion.id == payload.pabellon_id))
    if pavilion is None:
        raise ProblemDetailError(
            status=404,
            title="Pabellón no encontrado",
            detail="El pabellón asociado al stand no existe.",
            problem_type="https://exponexo.co/problemas/pabellon-no-encontrado",
        )

    code_upper = payload.codigo.strip().upper()
    dup = db.scalar(
        select(Stand).where(
            Stand.pabellon_id == payload.pabellon_id,
            Stand.codigo == code_upper,
        )
    )
    if dup is not None:
        raise ProblemDetailError(
            status=409,
            title="Código de stand duplicado",
            detail="Ya existe un stand con ese código dentro del mismo pabellón.",
            problem_type="https://exponexo.co/problemas/stand-duplicado",
        )

    stand = Stand(
        pabellon_id=payload.pabellon_id,
        codigo=code_upper,
        metros_cuadrados=payload.metros_cuadrados,
        tipo=payload.tipo,
        precio_base=payload.precio_base,
        fila=payload.fila,
        columna=payload.columna,
    )
    db.add(stand)
    db.commit()
    db.refresh(stand)
    return stand


def update_stand(db: Session, stand_id: str, payload: StandUpdateRequest) -> Stand:
    stand = db.scalar(select(Stand).where(Stand.id == stand_id))
    if stand is None:
        raise ProblemDetailError(
            status=404,
            title="Stand no encontrado",
            detail="El stand indicado no existe.",
            problem_type="https://exponexo.co/problemas/stand-no-encontrado",
        )
    if payload.codigo is not None:
        stand.codigo = payload.codigo.strip().upper()
    if payload.metros_cuadrados is not None:
        stand.metros_cuadrados = payload.metros_cuadrados
    if payload.tipo is not None:
        stand.tipo = payload.tipo
    if payload.precio_base is not None:
        stand.precio_base = payload.precio_base
    if payload.fila is not None:
        stand.fila = payload.fila
    if payload.columna is not None:
        stand.columna = payload.columna

    db.commit()
    db.refresh(stand)
    return stand


def list_event_stands_with_status(
    db: Session,
    event_id_or_slug: str,
) -> list[EventStandStatusResponse]:
    expire_overdue_reservations(db)
    event = get_event_by_slug_or_id(db, event_id_or_slug)

    stands = list(
        db.scalars(
            select(Stand).order_by(Stand.pabellon_id.asc(), Stand.fila.asc(), Stand.columna.asc())
        )
    )
    pavilions = {
        p.id: p.nombre for p in db.scalars(select(Pavilion))
    }
    active_reservations = list(
        db.scalars(
            select(StandReservation).where(
                StandReservation.evento_id == event.id,
                StandReservation.estado.in_(["pendiente_pago", "pagada"]),
            )
        )
    )
    status_by_stand: dict[str, str] = {}
    for res in active_reservations:
        status_by_stand[res.stand_id] = "pagado" if res.estado == "pagada" else "reservado"

    result: list[EventStandStatusResponse] = []
    for s in stands:
        state = status_by_stand.get(s.id, "disponible")
        result.append(
            EventStandStatusResponse(
                id=s.id,
                pabellon_id=s.pabellon_id,
                pabellon_nombre=pavilions.get(s.pabellon_id, "Pabellón"),
                codigo=s.codigo,
                metros_cuadrados=s.metros_cuadrados,
                tipo=s.tipo,
                precio_base=s.precio_base,
                fila=s.fila,
                columna=s.columna,
                estado=state,  # type: ignore[arg-type]
            )
        )
    return result


def reserve_stand(
    db: Session,
    user: User,
    payload: ReservationCreateRequest,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> StandReservation:
    """
    Reserve a stand atomically using `dbo.reservar_stand` on SQL Server
    or an equivalent atomic transaction + filtered unique constraint on SQLite.
    """
    expire_overdue_reservations(db)

    # Check idempotency key first: if same user already submitted this key, return same reservation
    clean_key = idempotency_key.strip()[:64]
    existing_idem = db.scalar(
        select(StandReservation).where(
            StandReservation.usuario_id == user.id,
            StandReservation.clave_idempotencia == clean_key,
        )
    )
    if existing_idem is not None:
        return existing_idem

    settings = get_settings()
    company_id = payload.empresa_id or user.empresa_id
    new_res_id = str(uuid.uuid4())
    outbox_id = str(uuid.uuid4())
    dialect = db.bind.dialect.name if db.bind else "sqlite"

    if dialect == "mssql":
        try:
            db.execute(
                text(
                    """
                    DECLARE @monto DECIMAL(12,2), @vence DATETIME2;
                    EXEC dbo.reservar_stand
                        @reserva_id = :reserva_id,
                        @evento_id = :evento_id,
                        @stand_id = :stand_id,
                        @empresa_id = :empresa_id,
                        @usuario_id = :usuario_id,
                        @minutos_vencimiento = :minutos_vencimiento,
                        @clave_idempotencia = :clave_idempotencia,
                        @correlacion_id = :correlacion_id,
                        @evento_salida_id = :evento_salida_id,
                        @monto_out = @monto OUTPUT,
                        @vence_en_out = @vence OUTPUT;
                    """
                ),
                {
                    "reserva_id": new_res_id,
                    "evento_id": payload.evento_id,
                    "stand_id": payload.stand_id,
                    "empresa_id": company_id,
                    "usuario_id": user.id,
                    "minutos_vencimiento": settings.reservation_expiration_minutes,
                    "clave_idempotencia": clean_key,
                    "correlacion_id": correlation_id,
                    "evento_salida_id": outbox_id,
                },
            )
            db.commit()
        except (IntegrityError, OperationalError, ProgrammingError) as exc:
            db.rollback()
            msg = str(exc)
            if "50001" in msg:
                raise ProblemDetailError(
                    status=400,
                    title="Evento no disponible",
                    detail="El evento no existe o no está publicado para reservas.",
                    problem_type="https://exponexo.co/problemas/evento-no-disponible",
                ) from exc
            if "50002" in msg:
                raise ProblemDetailError(
                    status=404,
                    title="Stand no encontrado",
                    detail="El stand indicado no existe.",
                    problem_type="https://exponexo.co/problemas/stand-no-encontrado",
                ) from exc
            raise ProblemDetailError(
                status=409,
                title="Stand no disponible",
                detail="El stand ya está reservado o pagado en este evento.",
                problem_type="https://exponexo.co/problemas/stand-ocupado",
            ) from exc

        reservation = db.scalar(
            select(StandReservation).where(StandReservation.id == new_res_id)
        )
        assert reservation is not None
        return reservation

    # Atomic transaction execution (SQLite / local test mode)
    event = db.scalar(select(Event).where(Event.id == payload.evento_id))
    if event is None or event.estado not in ("publicado", "en_curso"):
        raise ProblemDetailError(
            status=400,
            title="Evento no disponible",
            detail="El evento no existe o no está publicado para reservas.",
            problem_type="https://exponexo.co/problemas/evento-no-disponible",
        )

    stand = db.scalar(select(Stand).where(Stand.id == payload.stand_id))
    if stand is None:
        raise ProblemDetailError(
            status=404,
            title="Stand no encontrado",
            detail="El stand indicado no existe.",
            problem_type="https://exponexo.co/problemas/stand-no-encontrado",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.reservation_expiration_minutes)
    reservation = StandReservation(
        id=new_res_id,
        evento_id=event.id,
        stand_id=stand.id,
        empresa_id=company_id,
        usuario_id=user.id,
        estado="pendiente_pago",
        monto=Decimal(str(stand.precio_base)),
        vence_en=expires_at,
        clave_idempotencia=clean_key,
        version=1,
    )
    db.add(reservation)
    db.add(
        OutboxEvent(
            id=outbox_id,
            tipo="reserva.creada",
            carga=json.dumps(
                {
                    "reserva_id": new_res_id,
                    "evento_id": event.id,
                    "stand_id": stand.id,
                    "usuario_id": user.id,
                    "monto": str(stand.precio_base),
                    "vence_en": expires_at.isoformat(),
                },
                ensure_ascii=False,
            ),
            correlacion_id=correlation_id,
        )
    )
    db.add(
        AuditLog(
            usuario_id=user.id,
            accion="reserva.creada",
            entidad="reservas_stand",
            entidad_id=new_res_id,
            detalle=f"Stand {stand.codigo} reservado en evento {event.slug}",
            correlacion_id=correlation_id,
        )
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Check if concurrent request had the same idempotency key
        existing_retry = db.scalar(
            select(StandReservation).where(
                StandReservation.usuario_id == user.id,
                StandReservation.clave_idempotencia == clean_key,
            )
        )
        if existing_retry is not None:
            return existing_retry
        raise ProblemDetailError(
            status=409,
            title="Stand no disponible",
            detail="El stand ya se encuentra reservado o pagado en este evento.",
            problem_type="https://exponexo.co/problemas/stand-ocupado",
        ) from exc

    db.refresh(reservation)
    return reservation


def cancel_pending_reservation(
    db: Session,
    user: User,
    reservation_id: str,
    correlation_id: str | None = None,
) -> StandReservation:
    reservation = db.scalar(
        select(StandReservation).where(StandReservation.id == reservation_id)
    )
    if reservation is None or reservation.usuario_id != user.id:
        raise ProblemDetailError(
            status=404,
            title="Reserva no encontrada",
            detail="No se encontró la reserva solicitada.",
            problem_type="https://exponexo.co/problemas/reserva-no-encontrada",
        )
    if reservation.estado != "pendiente_pago":
        raise ProblemDetailError(
            status=409,
            title="No se puede cancelar la reserva",
            detail="Solo se pueden cancelar reservas en estado pendiente de pago.",
            problem_type="https://exponexo.co/problemas/reserva-no-cancelable",
        )

    reservation.estado = "cancelada"
    reservation.version += 1
    db.add(
        AuditLog(
            usuario_id=user.id,
            accion="reserva.cancelada",
            entidad="reservas_stand",
            entidad_id=reservation.id,
            detalle="Reserva cancelada por el expositor",
            correlacion_id=correlation_id,
        )
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def mark_reservation_paid(
    db: Session,
    reservation_id: str,
    payment_order_id: str,
    received_event_id: str,
    correlation_id: str | None = None,
) -> StandReservation:
    """Idempotently mark a reservation as paid (from `pago.aprobado`)."""
    reservation = db.scalar(
        select(StandReservation).where(StandReservation.id == reservation_id)
    )
    if reservation is None:
        raise ProblemDetailError(
            status=404,
            title="Reserva no encontrada",
            detail="La reserva indicada no existe.",
            problem_type="https://exponexo.co/problemas/reserva-no-encontrada",
        )

    dialect = db.bind.dialect.name if db.bind else "sqlite"
    outbox_id = str(uuid.uuid4())

    if dialect == "mssql":
        db.execute(
            text(
                """
                EXEC dbo.marcar_reserva_pagada
                    @reserva_id = :reserva_id,
                    @orden_pago_id = :orden_pago_id,
                    @evento_recibido_id = :evento_recibido_id,
                    @evento_salida_id = :evento_salida_id,
                    @correlacion_id = :correlacion_id;
                """
            ),
            {
                "reserva_id": reservation_id,
                "orden_pago_id": payment_order_id,
                "evento_recibido_id": received_event_id,
                "evento_salida_id": outbox_id,
                "correlacion_id": correlation_id,
            },
        )
        db.commit()
        db.refresh(reservation)
        return reservation

    already = db.scalar(
        select(ProcessedEvent).where(ProcessedEvent.evento_id == received_event_id)
    )
    if already is not None:
        return reservation

    reservation.estado = "pagada"
    reservation.orden_pago_id = payment_order_id
    reservation.version += 1
    db.add(ProcessedEvent(evento_id=received_event_id))
    db.add(
        OutboxEvent(
            id=outbox_id,
            tipo="reserva.pagada",
            carga=json.dumps(
                {
                    "reserva_id": reservation.id,
                    "evento_id": reservation.evento_id,
                    "stand_id": reservation.stand_id,
                    "orden_pago_id": payment_order_id,
                },
                ensure_ascii=False,
            ),
            correlacion_id=correlation_id,
        )
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def expire_overdue_reservations(
    db: Session,
    cutoff_time: datetime | None = None,
) -> int:
    """
    Expire `pendiente_pago` reservations whose `vence_en <= cutoff_time`
    and release their stands so they become available again.
    """
    now = _ensure_utc(cutoff_time) if cutoff_time else datetime.now(timezone.utc)
    overdue = list(
        db.scalars(
            select(StandReservation).where(
                StandReservation.estado == "pendiente_pago",
            )
        )
    )
    expired_count = 0
    for res in overdue:
        if _ensure_utc(res.vence_en) <= now:
            res.estado = "vencida"
            res.version += 1
            res.actualizado_en = now
            db.add(
                OutboxEvent(
                    tipo="reserva.vencida",
                    carga=json.dumps(
                        {
                            "reserva_id": res.id,
                            "evento_id": res.evento_id,
                            "stand_id": res.stand_id,
                            "usuario_id": res.usuario_id,
                        },
                        ensure_ascii=False,
                    ),
                )
            )
            expired_count += 1

    if expired_count > 0:
        db.commit()
    return expired_count
