# Catálogo de eventos de ExpoNexo

Los servicios no se llaman entre sí: publican **eventos** en una cola y quien está interesado los
consume. Este catálogo dice qué eventos existen, quién los publica, quién los consume y qué datos
llevan.

## 1. Forma común de un evento (sobre)

Todo evento viaja con los mismos campos de cabecera; solo cambia `datos`:

| Campo | Descripción |
|---|---|
| id | Identificador único global del evento (sirve para la idempotencia). |
| tipo | Nombre `entidad.accion` en pasado. |
| version | Versión del formato de `datos` (empieza en 1). |
| ocurrido_en | Fecha y hora UTC. |
| origen | Servicio que lo publicó. |
| correlacion_id | Para seguir la operación de punta a punta. |
| datos | Contenido propio del evento (tabla de abajo). |

Estudia: «CloudEvents specification» (un estándar real para esta forma) y «event versioning».

## 2. Eventos

| Tipo | Publica | Consume | Datos principales | Efecto |
|---|---|---|---|---|
| `cuenta.creada` | identidad-reservas | avisos | usuario, correo, nombre | Correo de bienvenida. |
| `reserva.creada` | identidad-reservas | avisos | reserva, evento, stand, monto, vence_en | Correo «tienes X minutos para pagar». |
| `reserva.vencida` | identidad-reservas | avisos | reserva, stand | Correo de reserva vencida. |
| `reserva.pagada` | identidad-reservas | avisos | reserva, evento, stand | Confirmación al expositor. |
| `pago.aprobado` | pagos | repartidor, avisos | orden, referencia, origen, monto, factura | El repartidor marca pagada la reserva o activa la entrada; avisos envía la factura. |
| `pago.rechazado` | pagos | avisos | orden, referencia, motivo | Aviso al comprador. |
| `pago.reembolsado` | pagos | repartidor, avisos | orden, referencia, monto | Libera el stand o cancela la entrada. |
| `entrada.activada` | identidad-reservas | avisos | entrada, evento | Correo con el QR de ingreso. |
| `cita.aceptada` | identidad-reservas | avisos | cita, inicio, fin, participantes | Correo a ambas personas. |
| `ticket.creado` | mesa-ayuda | avisos | ticket, prioridad, ubicacion | Telegram al personal si es alta o crítica. |
| `ticket.sla_vencido` | mesa-ayuda | avisos | ticket, nivel | Telegram al personal y escalamiento. |
| `dispositivo.caido` | mesa-ayuda | avisos | dispositivo, ubicacion, ticket | Telegram al personal. |

## 3. Reglas

1. **Se publica desde la bandeja de salida**, nunca directo en la transacción (ver
   [ARQUITECTURA.md](ARQUITECTURA.md), principio 4).
2. **El consumidor es idempotente:** antes de actuar, revisa si el `id` ya está en
   `eventos_procesados`.
3. **Reintentos y cola de errores:** si un consumidor falla, la cola reintenta; tras 3 intentos el
   mensaje pasa a la cola de errores para revisarlo a mano.
4. **Datos mínimos:** el evento lleva lo necesario para actuar. Nunca contraseñas, códigos,
   tokens ni datos de pago.
5. **Cambios compatibles:** agregar campos no rompe a nadie; quitar o renombrar requiere subir
   `version`.

## 4. Qué estudiar

«transactional outbox», «at-least-once delivery», «idempotent consumer», «Amazon SQS
visibility timeout», «dead-letter queue redrive», «AWS Lambda SQS batch size partial batch
response».
