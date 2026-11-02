from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class PurchaseTicketRequest(BaseModel):
    tipo: Literal["general", "negocios", "prensa"] = "general"


class TicketResponse(BaseModel):
    id: str
    evento_id: str
    evento_nombre: str | None = None
    usuario_id: str
    tipo: str
    estado: str
    precio_sugerido: Decimal
    orden_pago_id: str | None = None
    codigo_qr: str | None = None
    usada_en: datetime | None = None
    usada_en_dispositivo: str | None = None
    creada_en: datetime


class ActivateTicketInternalRequest(BaseModel):
    orden_pago_id: str
    evento_id: str | None = None


class ValidateTicketQrRequest(BaseModel):
    codigo_qr: str = Field(..., min_length=10, max_length=512)
    dispositivo_id: str = Field(default="puerta-principal-01", max_length=64)


class ValidateTicketQrResponse(BaseModel):
    valida: bool
    entrada_id: str
    evento_id: str
    usuario_id: str
    tipo: str
    estado: str
    usada_en: datetime
    usada_en_dispositivo: str


class CreateMeetingRoomRequest(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=32)
    capacidad: int = Field(default=4, gt=0, le=100)


class MeetingRoomResponse(BaseModel):
    id: str
    pabellon_id: str
    codigo: str
    capacidad: int


class TimeBlockItem(BaseModel):
    desde: datetime
    hasta: datetime


class UpdateAvailabilityRequest(BaseModel):
    bloques: list[TimeBlockItem]


class AvailabilityResponse(BaseModel):
    id: str
    usuario_id: str
    evento_id: str
    desde: datetime
    hasta: datetime


class FreeSlotResponse(BaseModel):
    expositor_id: str
    expositor_nombre: str
    empresa_nombre: str | None = None
    desde: datetime
    hasta: datetime


class ProposeAppointmentRequest(BaseModel):
    evento_id: str
    anfitrion_id: str
    inicio: datetime
    fin: datetime
    mensaje: str | None = Field(default=None, max_length=500)


class RespondAppointmentRequest(BaseModel):
    decision: Literal["aceptar", "rechazar"]


class AppointmentResponse(BaseModel):
    id: str
    evento_id: str
    solicitante_id: str
    solicitante_nombre: str | None = None
    anfitrion_id: str
    anfitrion_nombre: str | None = None
    sala_id: str | None = None
    sala_codigo: str | None = None
    inicio: datetime
    fin: datetime
    estado: str
    mensaje: str | None = None
    creada_en: datetime
