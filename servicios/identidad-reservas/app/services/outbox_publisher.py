import asyncio
from datetime import datetime, timezone
from functools import lru_cache
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.identity import OutboxEvent

logger = logging.getLogger("exponexo.identidad.outbox")


def build_cloud_event_envelope(outbox_row: OutboxEvent, origin: str = "identidad-reservas") -> dict[str, Any]:
    created_iso = (
        outbox_row.creado_en.astimezone(timezone.utc).isoformat()
        if outbox_row.creado_en.tzinfo
        else outbox_row.creado_en.replace(tzinfo=timezone.utc).isoformat()
    )
    return {
        "id": outbox_row.id,
        "tipo": outbox_row.tipo,
        "version": 1,
        "ocurrido_en": created_iso,
        "origen": origin,
        "correlacion_id": outbox_row.correlacion_id,
        "datos": json.loads(outbox_row.carga),
    }


@lru_cache
def _sns_client() -> Any:
    import boto3

    return boto3.client("sns", region_name=settings.aws_region)


def publish_pending_outbox_events(
    db: Session,
    max_batch: int = 50,
    sns_client: Any = None,
) -> dict[str, int]:
    """
    Lee los eventos pendientes de `bandeja_salida`, los publica en el tema SNS de eventos
    (o los registra en modo local si no hay tema configurado) y marca `publicado_en`.
    """
    pending = list(
        db.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.publicado_en.is_(None))
            .order_by(OutboxEvent.creado_en.asc())
            .limit(max_batch)
        ).all()
    )

    published_count = 0
    failed_count = 0
    topic_arn = (settings.sns_events_topic_arn or "").strip()

    for row in pending:
        try:
            body = json.dumps(build_cloud_event_envelope(row), ensure_ascii=False)
            if topic_arn:
                (sns_client or _sns_client()).publish(
                    TopicArn=topic_arn,
                    Message=body,
                    MessageAttributes={"tipo": {"DataType": "String", "StringValue": row.tipo}},
                )
            else:
                logger.info("Outbox local simulado [%s]: %s", row.tipo, row.id)

            row.publicado_en = datetime.now(timezone.utc)
            row.intentos = int(row.intentos or 0) + 1
            published_count += 1
        except Exception as exc:
            logger.error("Error al publicar evento outbox %s: %s", row.id, exc)
            row.intentos = int(row.intentos or 0) + 1
            failed_count += 1

    if pending:
        db.commit()

    return {
        "publicados": published_count,
        "fallidos": failed_count,
    }


_publishing = asyncio.Lock()


async def publish_after_write() -> None:
    """Publica la bandeja justo después de una operación que escribe.

    No hay sondeo periódico: consultar la base cada pocos segundos la mantendría despierta y
    consumiría su cuota gratuita (Azure SQL se pausa sola sin uso). Tras una escritura la base ya
    está despierta; un evento que falle se reintenta con la siguiente escritura.
    """
    if _publishing.locked():
        return
    from app.db import SessionLocal

    def publish_once() -> None:
        with SessionLocal() as db:
            publish_pending_outbox_events(db)

    async with _publishing:
        try:
            await asyncio.to_thread(publish_once)
        except Exception as exc:
            logger.error("Publicación de la bandeja falló: %s", exc)
