from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterAccountRequest(BaseModel):
    correo: EmailStr
    nombre: str = Field(min_length=2, max_length=120)
    contrasena: str = Field(min_length=10, max_length=128)
    rol: Literal["visitante", "expositor"] = "visitante"


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    correo: str
    nombre: str
    rol: str
    activo: bool
    correo_verificado: bool
    creado_en: datetime


class ConfirmEmailRequest(BaseModel):
    correo: EmailStr
    codigo: str = Field(min_length=6, max_length=12)


class PasswordRecoveryRequest(BaseModel):
    correo: EmailStr
    codigo: str | None = None
    nueva_contrasena: str | None = Field(default=None, min_length=10, max_length=128)


class LoginStep1Request(BaseModel):
    correo: EmailStr
    contrasena: str


class LoginStep1Response(BaseModel):
    pase_segundo_paso: str
    vence_en_segundos: int
    metodos_disponibles: list[str]
    metodo_preferido: str
    requiere_configurar_mfa: bool


class LoginStep2Request(BaseModel):
    metodo: Literal["app", "correo", "respaldo"]
    codigo: str = Field(min_length=6, max_length=16)


class TokenPairResponse(BaseModel):
    token_acceso: str
    token_refresco: str
    tipo_token: str = "Bearer"
    vence_en_segundos: int
    usuario: AccountResponse


class RefreshTokenRequest(BaseModel):
    token_refresco: str


class LogoutRequest(BaseModel):
    token_refresco: str


class ServiceTokenRequest(BaseModel):
    servicio: str = Field(min_length=2, max_length=60)
    secreto_interno: str = Field(min_length=8)


class ServiceTokenResponse(BaseModel):
    token_servicio: str
    tipo_token: str = "Bearer"
    vence_en_segundos: int


class MfaFactorInfo(BaseModel):
    tipo: str
    activo: bool
    preferido: bool
    creado_en: datetime


class PasskeyInfo(BaseModel):
    id: str
    nombre_dispositivo: str
    creada_en: datetime
    ultimo_uso_en: datetime | None


class SessionInfo(BaseModel):
    id: str
    creada_en: datetime
    vence_en: datetime
    agente: str | None


class SecurityProfileResponse(BaseModel):
    usuario: AccountResponse
    metodos_mfa: list[MfaFactorInfo]
    metodo_preferido: str | None
    codigos_respaldo_disponibles: int
    llaves_acceso: list[PasskeyInfo]
    sesiones_activas: list[SessionInfo]


class TotpSetupResponse(BaseModel):
    secreto: str
    otpauth_url: str
    qr_datos_url: str


class TotpConfirmRequest(BaseModel):
    codigo: str = Field(min_length=6, max_length=6)


class SetPreferredMfaRequest(BaseModel):
    tipo: Literal["app", "correo"]


class BackupCodesResponse(BaseModel):
    codigos: list[str]


class PasskeyOptionsResponse(BaseModel):
    opciones: dict[str, Any]
    desafio_token: str


class PasskeyRegisterRequest(BaseModel):
    nombre_dispositivo: str = Field(min_length=2, max_length=60)
    desafio_token: str
    credencial: dict[str, Any]


class PasskeyLoginOptionsRequest(BaseModel):
    correo: EmailStr


class PasskeyLoginVerifyRequest(BaseModel):
    correo: EmailStr
    desafio_token: str
    credencial: dict[str, Any]
