from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


SQLSERVER_LOGIN_TIMEOUT_SECONDS = 90


class Base(DeclarativeBase):
    pass


def build_engine(database_uri: str | None = None):
    uri = database_uri or get_settings().sqlalchemy_database_uri
    if uri.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        # Azure SQL sin uso se pausa y tarda hasta un minuto en despertar: tiempo de ingreso amplio
        connect_args = {"timeout": SQLSERVER_LOGIN_TIMEOUT_SECONDS}
    return create_engine(uri, pool_pre_ping=True, connect_args=connect_args)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
