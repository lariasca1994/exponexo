from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
import app.models  # noqa: F401
from app.models.identity import AuditLog, LoginAttempt, OutboxEvent
from app.services.depuracion import purge


def test_purge_removes_only_records_older_than_15_days():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    ahora = datetime(2026, 11, 16, tzinfo=timezone.utc)
    viejo, reciente = ahora - timedelta(days=20), ahora - timedelta(days=3)
    with sessionmaker(bind=engine)() as db:
        db.add_all([
            LoginAttempt(correo_huella="a", ip_huella="b", exito=False, ocurrido_en=viejo),
            LoginAttempt(correo_huella="a", ip_huella="b", exito=True, ocurrido_en=reciente),
            AuditLog(accion="ingreso", entidad="usuarios", entidad_id="1", ocurrido_en=viejo),
            OutboxEvent(tipo="x", carga="{}", creado_en=viejo, publicado_en=viejo),
            OutboxEvent(tipo="x", carga="{}", creado_en=viejo, publicado_en=None),  # pendiente: se conserva
        ])
        db.commit()

        borrados = purge(db, now=ahora)

        assert borrados["intentos_ingreso"] == 1
        assert borrados["auditoria"] == 1
        assert borrados["bandeja_salida"] == 1
        assert db.scalar(select(func.count()).select_from(LoginAttempt)) == 1
        assert db.scalar(select(func.count()).select_from(OutboxEvent)) == 1
