"""Depuración quincenal de identidad (regla del portafolio: 15 días).

Borra lo que solo sirve por un tiempo y que, acumulado, llenaría la base gratuita:
  - eventos de seguridad: intentos de ingreso y auditoría con más de 15 días;
  - códigos de verificación usados o vencidos, y sesiones vencidas o revocadas, con más de 15 días;
  - eventos ya publicados de la bandeja de salida y eventos ya procesados, con más de 15 días.
Nunca toca cuentas, reservas, entradas, citas ni eventos pendientes de publicar.

Lo ejecuta el workflow de depuración (días 1 y 16), no el contenedor: así la base solo despierta
para esto dos veces al mes.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, or_
from sqlalchemy.orm import Session

from app.models.identity import AuditLog, LoginAttempt, OutboxEvent, ProcessedEvent, UserSession, VerificationCode

DIAS_RETENCION = 15


def purge(db: Session, now: datetime | None = None) -> dict[str, int]:
    limite = (now or datetime.now(timezone.utc)) - timedelta(days=DIAS_RETENCION)
    sentencias = {
        "intentos_ingreso": delete(LoginAttempt).where(LoginAttempt.ocurrido_en < limite),
        "auditoria": delete(AuditLog).where(AuditLog.ocurrido_en < limite),
        "codigos_verificacion": delete(VerificationCode).where(
            or_(VerificationCode.usado_en < limite, VerificationCode.vence_en < limite)
        ),
        "sesiones": delete(UserSession).where(
            or_(UserSession.vence_en < limite, UserSession.revocada_en < limite)
        ),
        "bandeja_salida": delete(OutboxEvent).where(
            and_(OutboxEvent.publicado_en.is_not(None), OutboxEvent.publicado_en < limite)
        ),
        "eventos_procesados": delete(ProcessedEvent).where(ProcessedEvent.procesado_en < limite),
    }
    borrados = {tabla: db.execute(sentencia).rowcount or 0 for tabla, sentencia in sentencias.items()}
    db.commit()
    return borrados


def main() -> None:
    from app.db import SessionLocal

    with SessionLocal() as db:
        for tabla, cantidad in purge(db).items():
            print(f"{tabla}: {cantidad} registros con más de {DIAS_RETENCION} días borrados")


if __name__ == "__main__":
    main()
