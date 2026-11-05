from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 1. General
    app_environment: str = Field(
        default="desarrollo",
        validation_alias=AliasChoices("APP_ENTORNO", "ENTORNO"),
    )
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

    # 7. Events topic (AWS SNS, fan-out to the SQS queues of the event functions)
    aws_region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    sns_events_topic_arn: str = Field(default="", validation_alias="SNS_TEMA_EVENTOS_ARN")

    # 8. Internal Routes
    internal_secret: str = Field(default="", validation_alias="INTERNO_SECRETO")

    # Telegram: bot de avisos; cada persona vincula su chat desde su perfil
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")

    # 9. Business Rules
    reservation_expiration_minutes: int = Field(
        default=30,
        validation_alias="RESERVA_VENCIMIENTO_MINUTOS",
    )
    ticket_qr_signing_key: str = Field(default="", validation_alias="ENTRADA_QR_CLAVE_FIRMA")

    @property
    def is_production(self) -> bool:
        return self.app_environment.strip().casefold() == "produccion"

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if not self.is_production:
            return self

        def require_secret(value: str, name: str, minimum_length: int = 32) -> None:
            if len(value.strip()) < minimum_length:
                raise ValueError(f"{name} debe configurarse con al menos {minimum_length} caracteres")

        def is_placeholder(value: str) -> bool:
            normalized = value.strip().casefold()
            return not normalized or any(
                marker in normalized
                for marker in ("tu_", "changeme", "change-me", "example", "localhost", "dev-")
            )

        if self.database_url_override:
            parsed_database_url = urlparse(self.database_url_override)
            if parsed_database_url.scheme != "mssql+pyodbc":
                raise ValueError("DATABASE_URL debe apuntar a SQL Server en produccion")
            odbc_connect = parse_qs(parsed_database_url.query).get("odbc_connect", [])
            if odbc_connect:
                connection = odbc_connect[0].casefold()
                if any(
                    marker not in connection
                    for marker in ("server=", "database=", "uid=", "pwd=")
                ) or any(marker in connection for marker in ("tu_", "changeme", "example")):
                    raise ValueError("DATABASE_URL debe contener credenciales reales de SQL Server")
            elif not all(
                (parsed_database_url.hostname, parsed_database_url.path.strip("/"),
                 parsed_database_url.username, parsed_database_url.password)
            ):
                raise ValueError("DATABASE_URL debe incluir servidor, base y credenciales de SQL Server")
        else:
            database_values = (
                self.sqlserver_server,
                self.sqlserver_database,
                self.sqlserver_user,
                self.sqlserver_password,
                self.sqlserver_odbc_driver,
            )
            if any(is_placeholder(value) for value in database_values):
                raise ValueError("La configuracion real de SQL Server es obligatoria en produccion")
        if self.sqlalchemy_database_uri.startswith("sqlite"):
            raise ValueError("SQLite no esta permitido en produccion")

        issuer = urlparse(self.jwt_issuer)
        if issuer.scheme != "https" or not issuer.netloc:
            raise ValueError("JWT_EMISOR debe ser una URL HTTPS valida en produccion")
        if not self.jwt_audience.strip() or self.jwt_audience.strip().casefold() == "localhost":
            raise ValueError("JWT_AUDIENCIA es obligatoria en produccion")
        if is_placeholder(self.jwt_key_id):
            raise ValueError("JWT_CLAVE_ID debe configurarse en produccion")

        key_path = self.resolved_private_key_path
        if not key_path.is_file():
            raise ValueError("JWT_CLAVE_PRIVADA_RUTA debe apuntar a una clave RSA existente en produccion")
        try:
            private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        except (OSError, ValueError, TypeError) as exc:
            raise ValueError("JWT_CLAVE_PRIVADA_RUTA no contiene una clave privada valida") from exc
        if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size < 2048:
            raise ValueError("La clave JWT de produccion debe ser RSA de al menos 2048 bits")

        if not self.sns_events_topic_arn.startswith("arn:aws:sns:"):
            raise ValueError("SNS_TEMA_EVENTOS_ARN debe configurarse en produccion")

        require_secret(self.mfa_encryption_key, "MFA_CLAVE_CIFRADO")
        require_secret(self.ticket_qr_signing_key, "ENTRADA_QR_CLAVE_FIRMA")
        require_secret(self.internal_secret, "INTERNO_SECRETO")
        if any(
            "dev" in value.casefold()
            for value in (self.mfa_encryption_key, self.ticket_qr_signing_key, self.internal_secret)
        ):
            raise ValueError("Los secretos de desarrollo no estan permitidos en produccion")
        return self

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
            "Encrypt=yes;TrustServerCertificate=no;"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
