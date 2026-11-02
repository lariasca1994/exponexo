from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ProblemDetailError
from app.models.catalog import StandReservation
from app.models.identity import Company, User
from app.schemas.catalog import (
    CompanyCreateRequest,
    CompanyResponse,
    ReservationCreateRequest,
    ReservationResponse,
)
from app.security.dependencies import require_roles
from app.services.catalog_service import (
    cancel_pending_reservation,
    expire_overdue_reservations,
    reserve_stand,
    upsert_exhibitor_company,
)


router = APIRouter(tags=["Empresas y Reservas de Stands"])


@router.post(
    "/v1/empresas",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_my_company(
    payload: CompanyCreateRequest,
    current_user: User = Depends(require_roles("expositor", "administrador")),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = upsert_exhibitor_company(db=db, user=current_user, payload=payload)
    return CompanyResponse.model_validate(company)


@router.get("/v1/empresas/mia", response_model=CompanyResponse | None)
def get_my_company(
    current_user: User = Depends(require_roles("expositor", "administrador")),
    db: Session = Depends(get_db),
) -> CompanyResponse | None:
    if not current_user.empresa_id:
        return None
    company = db.scalar(select(Company).where(Company.id == current_user.empresa_id))
    return CompanyResponse.model_validate(company) if company else None


@router.post(
    "/v1/reservas",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stand_reservation(
    payload: ReservationCreateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(require_roles("expositor")),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    if not idempotency_key or not idempotency_key.strip():
        raise ProblemDetailError(
            status=400,
            title="Cabecera Idempotency-Key requerida",
            detail="Toda solicitud de reserva debe incluir la cabecera Idempotency-Key.",
            problem_type="https://exponexo.co/problemas/idempotency-key-requerida",
        )
    correlation_id = getattr(request.state, "correlation_id", None)
    reservation = reserve_stand(
        db=db,
        user=current_user,
        payload=payload,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
    )
    return ReservationResponse.model_validate(reservation)


@router.get("/v1/reservas/mias", response_model=list[ReservationResponse])
def list_my_reservations(
    current_user: User = Depends(require_roles("expositor")),
    db: Session = Depends(get_db),
) -> list[ReservationResponse]:
    expire_overdue_reservations(db)
    reservations = list(
        db.scalars(
            select(StandReservation)
            .where(StandReservation.usuario_id == current_user.id)
            .order_by(StandReservation.creado_en.desc())
        )
    )
    return [ReservationResponse.model_validate(r) for r in reservations]


@router.delete("/v1/reservas/{id}", response_model=ReservationResponse)
def cancel_my_reservation(
    id: str,
    request: Request,
    current_user: User = Depends(require_roles("expositor")),
    db: Session = Depends(get_db),
) -> ReservationResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    reservation = cancel_pending_reservation(
        db=db,
        user=current_user,
        reservation_id=id,
        correlation_id=correlation_id,
    )
    return ReservationResponse.model_validate(reservation)
