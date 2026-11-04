# Eventos entre servicios

Los servicios no se llaman entre sí para avisar cambios: cada uno guarda el evento en su **bandeja
de salida** dentro de la misma transacción del cambio y un publicador lo envía después al tema SNS
`exponexo-eventos`. El tema entrega cada evento, sin envoltura, a una cola SQS por función
(`exponexo-repartidor` y `exponexo-avisos`); tras 5 intentos fallidos el mensaje pasa a la cola de
errores de esa función (ADR-006 y ADR-018).

## Sobre

| Campo JSON | Descripción |
|---|---|
| `id` | UUID del evento, estable entre reintentos; los consumidores lo usan para no procesarlo dos veces. |
| `tipo` | `entidad.accion` en pasado y en español (ADR-012). |
| `version` | Versión del esquema de `datos`, empezando en 1. |
| `ocurrido_en` | Fecha y hora UTC en ISO 8601. |
| `origen` | Servicio productor: `identidad-reservas`, `pagos` o `mesa-ayuda`. |
| `correlacion_id` | Identificador de la operación de punta a punta (cabecera `X-Correlation-Id`). |
| `datos` | Propiedades del evento en `snake_case`. |

## Catálogo

| Tipo | Productor | Consumidores |
|---|---|---|
| `cuenta.creada` | identidad-reservas | avisos: bienvenida |
| `reserva.creada` | identidad-reservas | avisos: recordatorio de pago |
| `reserva.pagada` | identidad-reservas | avisos: confirmación |
| `reserva.vencida` | identidad-reservas | avisos: reserva vencida |
| `reserva.cancelada` | identidad-reservas | (ninguno por ahora) |
| `entrada.activada` | identidad-reservas | avisos: credencial de acceso |
| `cita.aceptada` | identidad-reservas | avisos: aviso a los participantes |
| `pago.aprobado` | pagos | repartidor: marca la reserva pagada o activa la entrada; avisos: factura |
| `pago.reembolsado` | pagos | repartidor: reembolsa la reserva o cancela la entrada; avisos: confirmación |
| `ticket.creado` | mesa-ayuda | avisos: Telegram al personal si la prioridad es alta |
| `ticket.sla_vencido` | mesa-ayuda | avisos: escalamiento |
| `dispositivo.caido` | mesa-ayuda | avisos: alerta al personal |

`avisos` también sabe atender `pago.rechazado`, pero pagos aún no lo publica.

## Reglas

- El repartidor llama a las rutas `/v1/interno/...` de identidad con un token de servicio
  (ADR-016); nunca con el token de una persona.
- Los consumidores responden por lote (`batchItemFailures`): solo se reintentan los mensajes que
  fallaron.
- Los avisos nunca incluyen contraseñas, códigos ni tokens; la función lo verifica antes de enviar.

*Estudia: «transactional outbox», «idempotent consumer», «Amazon SNS fan-out to SQS», «dead-letter
queue redrive», «AWS Lambda SQS partial batch response».*
