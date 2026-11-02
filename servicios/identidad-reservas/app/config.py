from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 1. General
    app_environment: str = Field(default="desarrollo", validation_alias="APP_ENTORNO")
    app_port: int = Field(default=8001, validation_alias="APP_PUERTO")
    app_log_level: str = Field(default="INFO", validation_alias="APP_NIVEL_LOGS")
    portal_url: str = Field(default="http://localhost:5173", validation_alias="PORTAL_URL")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="CORS_ORIGENES_PERMITIDOS",
    )

    # 2. Database (SQL Server / test override)
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")
    sqlserver_server: str = Field(
        default="TU_SERVIDOR.database.windows.net",
        validation_alias="SQLSERVER_SERVIDOR",
    )
    sqlserver_port: int = Field(default=1433, validation_alias="SQLSERVER_PUERTO")
    sqlserver_database: str = Field(default="TU_BASE", validation_alias="SQLSERVER_BASE")
    sqlserver_user: str = Field(default="TU_USUARIO", validation_alias="SQLSERVER_USUARIO")
    sqlserver_password: str = Field(default="TU_CONTRASENA", validation_alias="SQLSERVER_CONTRASENA")
    sqlserver_odbc_driver: str = Field(
        default="ODBC Driver 18 for SQL Server",
        validation_alias="SQLSERVER_DRIVER_ODBC",
    )

    # 3. Access Tokens (JWT RS256)
    jwt_issuer: str = Field(default="http://localhost:8001", validation_alias="JWT_EMISOR")
    jwt_audience: str = Field(default="exponexo", validation_alias="JWT_AUDIENCIA")
    jwt_key_id: str = Field(default="exponexo-2026-11", validation_alias="JWT_CLAVE_ID")
    jwt_private_key_path: str = Field(
        default="claves/jwt_privada.pem",
        validation_alias="JWT_CLAVE_PRIVADA_RUTA",
    )
    jwt_access_minutes: int = Field(default=15, validation_alias="JWT_ACCESO_MINUTOS")
    jwt_refresh_days: int = Field(default=7, validation_alias="JWT_REFRESCO_DIAS")

    # 4. Two-Factor Authentication (MFA)
    mfa_issuer_name: str = Field(default="ExpoNexo", validation_alias="MFA_EMISOR_NOMBRE")
    mfa_encryption_key: str = Field(default="", validation_alias="MFA_CLAVE_CIFRADO")
    mfa_pass_minutes: int = Field(default=5, validation_alias="MFA_PASE_MINUTOS")
    mfa_email_code_minutes: int = Field(default=10, validation_alias="MFA_CODIGO_CORREO_MINUTOS")
    mfa_max_attempts: int = Field(default=5, validation_alias="MFA_INTENTOS_MAXIMOS")
    mfa_lockout_minutes: int = Field(default=15, validation_alias="MFA_BLOQUEO_MINUTOS")

    # 5. Passkeys (WebAuthn)
    webauthn_rp_id: str = Field(default="localhost", validation_alias="WEBAUTHN_RP_ID")
    webauthn_rp_name: str = Field(default="ExpoNexo", validation_alias="WEBAUTHN_RP_NOMBRE")
    webauthn_origin_url: str = Field(
        default="http://localhost:5173",
        validation_alias="WEBAUTHN_ORIGEN_URL",
    )

    # 6. Email (Brevo)
    brevo_api_key: str = Field(default="", validation_alias="BREVO_API_KEY")
    brevo_sender_email: str = Field(default="no-responder@exponexo.co", validation_alias="BREVO_REMITENTE_CORREO")
    brevo_sender_name: str = Field(default="ExpoNexo", validation_alias="BREVO_REMITENTE_NOMBRE")

    # Cloudinary (Almacenamiento de imágenes: banners, planos y evidencias)
    cloudinary_cloud_name: str = Field(default="", validation_alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", validation_alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", validation_alias="CLOUDINARY_API_SECRET")

    # 7. Events Queue (AWS SQS)
    aws_region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    sqs_events_queue_url: str = Field(default="", validation_alias="SQS_COLA_EVENTOS_URL")

    # 8. Internal Routes
    internal_secret: str = Field(default="", validation_alias="INTERNO_SECRETO")

    # 9. Business Rules
    reservation_expiration_minutes: int = Field(
        default=30,
        validation_alias="RESERVA_VENCIMIENTO_MINUTOS",
    )
    ticket_qr_signing_key: str = Field(default="", validation_alias="ENTRADA_QR_CLAVE_FIRMA")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def resolved_private_key_path(self) -> Path:
        path = Path(self.jwt_private_key_path)
        if not path.is_absolute():
            return BASE_DIR / path
        return path

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        if self.sqlserver_server.startswith("TU_SERVIDOR"):
            # Local development SQLite fallback until Azure SQL credentials are configured
            return f"sqlite:///{(BASE_DIR / 'exponexo_local.db').as_posix()}"
        odbc_str = (
            f"DRIVER={{{self.sqlserver_odbc_driver}}};"
            f"SERVER=tcp:{self.sqlserver_server},{self.sqlserver_port};"
            f"DATABASE={self.sqlserver_database};"
            f"UID={self.sqlserver_user};"
            f"PWD={self.sqlserver_password};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

