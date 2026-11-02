from datetime import datetime, timezone
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


def publish_pending_outbox_events(
    db: Session,
    max_batch: int = 50,
    sqs_client: Any = None,
) -> dict[str, int]:
    """
    Lee los eventos pendientes de `bandeja_salida`, los envía a SQS (o los registra en modo local)
    y marca `publicado_en`.
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
    queue_url = (settings.sqs_events_queue_url or "").strip()

    for row in pending:
        try:
            envelope = build_cloud_event_envelope(row)
            body = json.dumps(envelope, ensure_ascii=False)
            if queue_url and sqs_client is not None:
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=body,
                )
            elif queue_url:
                import boto3  # type: ignore

                client = boto3.client("sqs", region_name=settings.aws_region or "us-east-1")
                client.send_message(QueueUrl=queue_url, MessageBody=body)
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
