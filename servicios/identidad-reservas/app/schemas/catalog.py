from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreateRequest(BaseModel):
    nit: str = Field(min_length=5, max_length=20)
    razon_social: str = Field(min_length=2, max_length=150)
    sector: str = Field(min_length=2, max_length=60)
    sitio_web: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=300)


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nit: str
    razon_social: str
    sector: str
    sitio_web: str | None
    logo_url: str | None


class EventCreateRequest(BaseModel):
    nombre: str = Field(min_length=3, max_length=150)
    slug: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9-]+$")
    descripcion: str = Field(default="", max_length=2000)
    inicio: datetime
    fin: datetime
    estado: Literal["borrador", "publicado", "en_curso", "finalizado", "cancelado"] = "publicado"
    precio_entrada: Decimal = Field(default=Decimal("45000.00"), ge=Decimal("0.00"))
    aforo: int = Field(default=1000, ge=1)
    imagen_url: str | None = Field(default=None, max_length=300)


class EventUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    inicio: datetime | None = None
    fin: datetime | None = None
    estado: Literal["borrador", "publicado", "en_curso", "finalizado", "cancelado"] | None = None
    precio_entrada: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    aforo: int | None = Field(default=None, ge=1)
    imagen_url: str | None = Field(default=None, max_length=300)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    slug: str
    descripcion: str
    inicio: datetime
    fin: datetime
    estado: str
    precio_entrada: Decimal
    aforo: int
    imagen_url: str | None = None
    creado_en: datetime


class PaginatedEventsResponse(BaseModel):
    pagina: int
    tamano: int
    total: int
    items: list[EventResponse]


class PavilionCreateRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    capacidad_stands: int = Field(ge=1, le=500)
    plano_url: str | None = Field(default=None, max_length=300)


class PavilionUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=60)
    capacidad_stands: int | None = Field(default=None, ge=1, le=500)
    plano_url: str | None = Field(default=None, max_length=300)


class PavilionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    capacidad_stands: int
    plano_url: str | None


class StandCreateRequest(BaseModel):
    pabellon_id: str
    codigo: str = Field(min_length=2, max_length=20)
    metros_cuadrados: Decimal = Field(gt=Decimal("0.00"))
    tipo: Literal["basico", "esquinero", "isla"] = "basico"
    precio_base: Decimal = Field(gt=Decimal("0.00"))
    fila: int = Field(default=1, ge=1, le=50)
    columna: int = Field(default=1, ge=1, le=50)


class StandUpdateRequest(BaseModel):
    codigo: str | None = Field(default=None, min_length=2, max_length=20)
    metros_cuadrados: Decimal | None = Field(default=None, gt=Decimal("0.00"))
    tipo: Literal["basico", "esquinero", "isla"] | None = None
    precio_base: Decimal | None = Field(default=None, gt=Decimal("0.00"))
    fila: int | None = Field(default=None, ge=1, le=50)
    columna: int | None = Field(default=None, ge=1, le=50)


class StandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pabellon_id: str
    codigo: str
    metros_cuadrados: Decimal
    tipo: str
    precio_base: Decimal
    fila: int
    columna: int


class EventStandStatusResponse(BaseModel):
    id: str
    pabellon_id: str
    pabellon_nombre: str
    codigo: str
    metros_cuadrados: Decimal
    tipo: str
    precio_base: Decimal
    fila: int
    columna: int
    estado: Literal["disponible", "reservado", "pagado"]


class ReservationCreateRequest(BaseModel):
    evento_id: str
    stand_id: str
    empresa_id: str | None = None


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evento_id: str
    stand_id: str
    empresa_id: str | None
    usuario_id: str
    estado: str
    monto: Decimal
    vence_en: datetime
    orden_pago_id: str | None
    creado_en: datetime


class InternalReservationResponse(BaseModel):
    id: str
    evento_id: str
    stand_id: str
    usuario_id: str
    empresa_id: str | None
    estado: str
    monto: Decimal
    vence_en: datetime


class MarkReservationPaidRequest(BaseModel):
    orden_pago_id: str = Field(min_length=1, max_length=64)
    evento_id: str = Field(min_length=1, max_length=36)
