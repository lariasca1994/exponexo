# Modelo de datos

Cada servicio es dueño de su base y ningún otro la lee (ADR-002). Tablas, columnas, colecciones y
campos están en español y en `snake_case` (ADR-012). Las llaves son UUID generados por la
aplicación y guardados como texto de 36 caracteres (ADR-013). Fechas en UTC.

## 1. Identidad, reservas y agenda · SQL Server (Azure SQL)

Migraciones con Alembic en `servicios/identidad-reservas/migraciones/`; el contenedor las aplica al
arrancar.

| Tabla | Contenido |
|---|---|
| `empresas` | Expositores: NIT, razón social, sector, sitio y logo |
| `usuarios` | Correo único, nombre, hash Argon2 de la contraseña, rol, empresa |
| `factores_mfa` | App autenticadora o correo por usuario; el secreto va cifrado |
| `codigos_verificacion` | Códigos de un solo uso (huella, intentos, vencimiento) |
| `codigos_respaldo` | Códigos de respaldo de MFA (solo su huella) |
| `llaves_acceso` | Llaves de acceso WebAuthn: credencial, clave pública, contador |
| `sesiones` | Tokens de refresco (huella), vencimiento y revocación |
| `intentos_ingreso` | Intentos por correo e IP, para bloquear fuerza bruta |
| `auditoria` | Quién hizo qué, sobre qué entidad y con qué correlación |
| `eventos` | Ferias: fechas, estado, precio de entrada y aforo |
| `pabellones` · `stands` | Plano del recinto: stands por pabellón con tipo, área y precio |
| `reservas_stand` | Reserva de un stand en un evento; un stand no puede tener dos reservas activas |
| `entradas` | Entradas de visitantes con su QR firmado |
| `salas` · `disponibilidad` · `citas` | Agenda de negocios entre expositores y visitantes |
| `bandeja_salida` · `eventos_procesados` | Eventos por publicar y eventos ya atendidos (idempotencia) |

Procedimientos almacenados (ADR-007): `reservar_stand`, `marcar_reserva_pagada`, `vencer_reservas`
y `aceptar_cita`. Concentran las reglas que deben ser atómicas: cupo del stand, cambio de estado y
evento en la bandeja de salida en una sola transacción.

## 2. Pagos y facturación · Oracle Autonomous Database

Esquema propio dentro de una base compartida, sin acceso a otros esquemas. Migraciones con Flyway
en `servicios/pagos/src/main/resources/db/migration/`.

| Objeto | Contenido |
|---|---|
| `ordenes_pago` | Orden por reserva o entrada: monto, estado, clave de idempotencia |
| `transacciones` | Intentos de pago de cada orden |
| `cobros_qr` | Cobros con QR firmado y su vigencia |
| `facturas` · `detalle_factura` | Factura con consecutivo legible (`seq_numero_factura`), impuestos y líneas |
| `reembolsos` | Devoluciones asociadas a una orden |
| `bandeja_salida` · `eventos_procesados` | Igual que en identidad |
| `pkg_facturacion` | Paquete PL/SQL: `emitir_factura` y `registrar_reembolso` |

## 3. Mesa de ayuda y monitoreo · MongoDB Atlas

Campos en `snake_case` (los mismos nombres del JSON de la API) y fechas como fechas BSON en UTC;
`_id` es el UUID en texto. `lecturas_dispositivo` es una colección de series de tiempo
(`momento` como campo de tiempo y `dispositivo_id` como metadato).

| Colección | Contenido |
|---|---|
| `tickets` | Ticket con su historial embebido, prioridad y SLA; número único |
| `politicas_sla` | Tiempos de atención por prioridad |
| `dispositivos` | Dispositivos del recinto con código único y último reporte |
| `lecturas_dispositivo` | Lecturas de alto volumen; se borran solas tras `LECTURA_RETENCION_DIAS` (índice TTL) |
| `bandeja_salida` | Eventos por publicar |

*Estudia: «database per service», «transactional outbox», «SQL Server filtered index», «Oracle
PL/SQL package», «MongoDB TTL index», «embedded vs referenced documents».*
