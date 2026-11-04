# Eventos entre servicios

Este catálogo define la **convención objetivo** para eventos nuevos o migrados. Los productores y
consumidores actuales todavía usan identificadores y sobres en español; esta página no afirma que
el formato objetivo ya esté desplegado.

## Sobre objetivo

| Campo JSON | Descripción |
|---|---|
| `id` | UUID estable del evento, usado para deduplicación. |
| `type` | Nombre técnico inglés `entity.action` en pasado. |
| `version` | Versión del esquema de `data`, empezando en 1. |
| `occurred_at` | Fecha y hora UTC. |
| `source` | Identificador inglés del servicio productor. |
| `correlation_id` | Correlación de la operación. |
| `data` | Propiedades del evento en inglés `snake_case`. |

UUID nuevos de evento se generan como UUID v7 en la aplicación; al persistir, usan la
representación correspondiente al motor (ver [MODELO-DE-DATOS.md](MODELO-DE-DATOS.md)). No
reemplazar IDs históricos ni derivar un ID nuevo en cada reintento.

## Catálogo objetivo y nombres actuales documentados

Los nombres actuales de la columna izquierda se encuentran en la documentación/código existente;
los de la derecha son la norma objetivo de ADR-012 y ADR-014. La tabla es un plan de transición,
no una afirmación de que todos los eventos enumerados ya se produzcan en runtime.

| Tipo actual | Tipo objetivo | Servicio productor | Consumidores/efecto previsto |
|---|---|---|---|
| `cuenta.creada` | `account.created` | identidad-reservas | avisos: bienvenida |
| `reserva.creada` | `reservation.created` | identidad-reservas | avisos: recordatorio de pago |
| `reserva.vencida` | `reservation.expired` | identidad-reservas | avisos: reserva vencida |
| `reserva.pagada` | `reservation.paid` | identidad-reservas | avisos: confirmación |
| `pago.aprobado` | `payment.approved` | pagos | repartidor y avisos: confirmar reserva/entrada y enviar factura |
| `pago.rechazado` | `payment.rejected` | pagos | avisos: informar rechazo |
| `pago.reembolsado` | `payment.refunded` | pagos | repartidor y avisos: aplicar reembolso |
| `entrada.activada` | `admission.activated` | identidad-reservas | avisos: credencial de acceso |
| `cita.aceptada` | `appointment.accepted` | identidad-reservas | avisos: notificar participantes |
| `ticket.creado` | `support_ticket.created` | mesa-ayuda | avisos: notificar al personal |
| `ticket.sla_vencido` | `support_ticket.sla_breached` | mesa-ayuda | avisos: alertar/escalar |
| `dispositivo.caido` | `device.offline` | mesa-ayuda | avisos: alertar al personal |

Ejemplo de `data` objetivo (nombres ilustrativos del esquema, no un mensaje actual):

```json
{
  "reservation_id": "UUID",
  "event_id": "UUID",
  "booth_id": "UUID",
  "amount": 125000.00,
  "expires_at": "2027-01-15T17:00:00Z"
}
```

Los valores reales deben definirse en el esquema de cada evento. Nunca incluir contraseñas,
códigos de acceso, tokens, secretos ni datos completos de pago. La información de una persona se
limita a lo estrictamente necesario para el consumidor autorizado.

## Compatibilidad y versionado

1. Identificar productores, consumidores, colas, DLQ, registros de deduplicación y cualquier
   replay/retención antes de cambiar el nombre o los campos.
2. Publicar el esquema inglés versionado y preparar adaptadores/consumidores que entiendan ambas
   formas durante una ventana coordinada. No asumir que renombrar un campo conserva el evento.
3. Mantener el `id` lógico estable a través de reintentos y traducciones; asegurar que la
   idempotencia impide procesar dos veces el mismo hecho aunque convivan representaciones.
4. Migrar todos los productores y consumidores; retirar la forma española solo tras comprobar que
   ya no se usa y acordar la fecha de retiro.
5. Si cambia un significado o se elimina/renombra un campo, incrementar `version`; agregar un
   campo opcional puede ser compatible solo si los consumidores ignoran campos desconocidos.

Los registros históricos de la bandeja de salida y de mensajes procesados no se alteran para
traducir nombres. Si deben reproducirse, usar un adaptador de lectura que conserve el evento
original y no provoque duplicados.

## Entrega, reintentos y estado verificado

La arquitectura prevista usa bandeja de salida y Amazon SQS. Los consumidores deben ser
idempotentes y tolerar entrega al menos una vez. Reintentos, número de intentos, visibilidad,
respuesta parcial por lote y política de DLQ se documentan como comportamiento implementado solo
después de verificar la configuración real de SQS/Lambda; el número de intentos no es universal ni
se puede inferir de este catálogo.

En el repositorio hay productores/consumidores con nombres actuales en español (por ejemplo,
`pago.aprobado`, `pago.reembolsado` y `cita.aceptada`); por ello, no cambies nombres de evento de
forma aislada ni declares conformidad completa con un estándar externo. Ver
[ARQUITECTURA.md](ARQUITECTURA.md) para el patrón de integración.

## Referencias de estudio

«transactional outbox», «at-least-once delivery», «idempotent consumer», «Amazon SQS visibility
timeout», «dead-letter queue redrive», «AWS Lambda SQS partial batch response».
