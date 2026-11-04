# Modelo de datos de ExpoNexo

Este es el **modelo objetivo** para esquemas nuevos o migrados. Los nombres de tablas,
colecciones, columnas y campos persistidos se expresan en inglés `snake_case`; la documentación
explicativa y los valores que ve una persona pueden permanecer en español. No es una descripción
literal del esquema que todos los servicios usan actualmente.

## Norma y estado de implementación

- Nuevas tablas y columnas relacionales: nombres en inglés `snake_case`.
- Nuevas colecciones y campos MongoDB: nombres en inglés `snake_case`.
- UUID nuevos: UUID v7 generado por la aplicación. SQL Server `uniqueidentifier`; Oracle
  `RAW(16)`; MongoDB UUID BSON `BinData` subtype 4. En JSON y mensajes se transporta su forma
  textual UUID canónica.
- Fechas persistidas en UTC; dinero en decimal de precisión fija, nunca punto flotante.
- Estados acotados con restricción o validación explícita; claves foráneas e índices adecuados.

**Evidencia actual:** el esquema/migración de Identidad incluye identificadores `String(36)` y
nombres españoles; el modelo JPA de Pagos declara, por ejemplo, `ordenes_pago`, `referencia` y
`usuario_id` como nombres de columna, con ID textual de hasta 36 caracteres; Mesa de ayuda usa
colecciones como `politicas_sla`, `dispositivos` y `lecturas_dispositivo`, y crea identificadores
como cadenas. Los generadores observados usan UUID v4 (`uuid.uuid4()`, `UUID.randomUUID()` y
`Guid.NewGuid()`), no UUID v7. Por tanto, este modelo documenta una **norma objetivo**, no una
alineación ya desplegada.

## Migración y conservación de datos

No se cambia un esquema histórico en el sitio ni se reescriben datos solo para traducir nombres o
cambiar UUID v4 por v7. Antes de migrar, inventariar filas, claves foráneas, índices, procedimientos,
vistas, jobs, consumidores y exportaciones; definir ventana, dueño, rollback y versión compatible.

Para cambiar nombres se recomienda una migración por expansión y contracción: crear el nombre
objetivo, copiar/backfill preservando valores, mantener lectura/escritura compatibles durante el
periodo acordado, verificar conteos y referencias, migrar productores/consumidores, y retirar el
nombre legado solo con evidencia de cero uso. Para UUID, conservar los valores lógicos y mantener
las referencias; al convertir una representación, usar conversión determinista y verificar
unicidad, relaciones y round-trip. No regenerar IDs. No aplicar simultáneamente una conversión de
tipo y una renominación destructiva sin una fase reversible y coordinada.

## 1. Identidad, reservas y agenda (SQL Server)

Tipos conceptuales; concretar longitudes, nulabilidad, restricciones e índices en migraciones.
`id` y las columnas `*_id` que refieren a una entidad usan `uniqueidentifier` en el objetivo.

| Tabla objetivo | Columnas principales |
|---|---|
| `users` | `id`, `email`, `name`, `password_hash`, `role`, `company_id`, `is_active`, `email_verified`, `created_at`, `updated_at` |
| `mfa_factors` | `id`, `user_id`, `factor_type`, `encrypted_secret`, `is_active`, `is_preferred`, `last_accepted_step`, `created_at` |
| `verification_codes` | `id`, `user_id`, `purpose`, `code_hash`, `failed_attempts`, `expires_at`, `used_at` |
| `backup_codes` | `id`, `user_id`, `code_hash`, `used_at` |
| `passkeys` | `id`, `user_id`, `credential_id`, `public_key`, `signature_counter`, `device_name`, `created_at`, `last_used_at` |
| `sessions` | `id`, `user_id`, `refresh_token_hash`, `created_at`, `expires_at`, `revoked_at`, `user_agent` |
| `login_attempts` | `id`, `email_hash`, `ip_hash`, `succeeded`, `occurred_at` |
| `companies` | `id`, `tax_id`, `legal_name`, `industry`, `website_url`, `logo_url` |
| `events` | `id`, `name`, `slug`, `description`, `starts_at`, `ends_at`, `status`, `admission_price`, `capacity` |
| `halls` | `id`, `name`, `booth_capacity`, `floor_plan_url` |
| `booths` | `id`, `hall_id`, `code`, `area_square_meters`, `booth_type`, `base_price`, `grid_row`, `grid_column` |
| `booth_reservations` | `id`, `event_id`, `booth_id`, `company_id`, `user_id`, `status`, `amount`, `expires_at`, `payment_order_id`, `row_version` |
| `admissions` | `id`, `event_id`, `user_id`, `status`, `access_code_hash`, `price`, `payment_order_id`, `used_at` |
| `meeting_rooms` | `id`, `name`, `capacity` |
| `availability_slots` | `id`, `event_id`, `user_id`, `starts_at`, `ends_at` |
| `appointments` | `id`, `event_id`, `requester_id`, `invitee_id`, `room_id`, `starts_at`, `ends_at`, `status`, `message` |
| `audit_log` | `id`, `user_id`, `action`, `entity_type`, `entity_id`, `details`, `correlation_id`, `occurred_at` |
| `outbox` | `id`, `event_type`, `payload`, `correlation_id`, `created_at`, `published_at`, `publish_attempts` |
| `processed_events` | `event_id`, `processed_at` |

Reglas de dominio:

- `email` es único; la dirección normalizada se guarda según una política explícita.
- En `mfa_factors`, cada usuario tiene como máximo un factor preferido por tipo permitido; la
  combinación (`user_id`, `factor_type`) es única.
- En `booth_reservations`, un stand no admite dos reservas activas para el mismo evento. Usar una
  restricción/índice filtrado que cubra `pending_payment` y `paid`; conservar la atomicidad de la
  reserva.
- `appointments` impide solapamientos aceptados para una misma persona.
- Montos usan decimal exacto; fechas y horas son UTC. Un número legible de negocio, si se requiere,
  no reemplaza el UUID de clave primaria.

## 2. Pagos y facturación (Oracle)

Las claves UUID objetivo se almacenan en `RAW(16)`; la forma de aplicación/API continúa siendo UUID.

| Tabla objetivo | Columnas principales |
|---|---|
| `payment_orders` | `id`, `reference_id`, `source_type`, `user_id`, `amount`, `currency`, `status`, `idempotency_key`, `created_at`, `updated_at` |
| `payment_transactions` | `id`, `order_id`, `payment_method`, `status`, `authorization_code`, `occurred_at` |
| `qr_charges` | `id`, `order_id`, `content_hash`, `expires_at`, `status` |
| `invoices` | `id`, `order_id`, `invoice_number`, `issued_at`, `customer_tax_id`, `customer_legal_name`, `subtotal`, `tax_amount`, `total`, `status` |
| `invoice_lines` | `id`, `invoice_id`, `description`, `quantity`, `unit_price`, `tax_amount` |
| `refunds` | `id`, `order_id`, `amount`, `reason`, `status`, `created_at` |
| `outbox` | `id`, `event_type`, `payload`, `correlation_id`, `created_at`, `published_at`, `publish_attempts` |
| `processed_events` | `event_id`, `processed_at` |

`amount`, `subtotal`, `tax_amount`, `total`, `quantity` y `unit_price` usan `NUMBER(p,s)` con
precisión y escala adecuadas al dominio. `invoice_number` es un consecutivo de negocio único,
asignado sin confundirlo con `invoices.id`. La lógica transaccional y el número de factura deben
mantener su consistencia al aplicar cambios de esquema.

## 3. Mesa de ayuda y monitoreo (MongoDB)

Colecciones y propiedades objetivo en inglés `snake_case`. Si la clave primaria es UUID, se
almacena como UUID BSON `BinData` subtype 4; los códigos legibles de ticket/dispositivo son campos
de negocio, no sustitutos del UUID.

| Colección objetivo | Documento/campos principales |
|---|---|
| `tickets` | `_id`, `ticket_number`, `title`, `description`, `category`, `priority`, `status`, `current_level`, `requester`, `assignee`, `location`, `sla`, `history`, `device_id`, `created_at`, `updated_at` |
| `sla_policies` | `_id`, `priority`, `response_hours`, `resolution_hours` |
| `devices` | `_id`, `device_code`, `device_type`, `location`, `status`, `last_reported_at`, `enrolled_at` |
| `device_readings` | `recorded_at` (time field), `device_id` (metadata), `cpu_percent`, `memory_percent`, `disk_percent`, `network_ok` |
| `alerts` | `_id`, `device_id`, `alert_type`, `started_at`, `ended_at`, `ticket_number` |
| `outbox` | `_id`, `event_type`, `payload`, `correlation_id`, `created_at`, `published_at`, `publish_attempts` |
| `processed_events` | `_id`/`event_id`, `processed_at` |

`tickets.history` conserva los cambios de estado con campos como `occurred_at`, `from_status`,
`to_status`, `note` y `actor_id`. Crear índices únicos para `ticket_number` y `device_code`, índices
de consulta para estado/prioridad/SLA, y retención TTL/time-series para `device_readings` de acuerdo
con la política aprobada. No asumir el valor de retención del diseño como valor configurado en cada
entorno: la aplicación actual lee `LECTURA_RETENCION_DIAS` y aplica un default si falta.

## 4. Procedimientos y nombres existentes

Los nombres objetivo de procedimientos también son inglés `snake_case`:

| Base | Nombre objetivo | Responsabilidad |
|---|---|---|
| SQL Server | `reserve_booth` | Validar disponibilidad, crear reserva pendiente y registrar el evento en `outbox` atómicamente. |
| Oracle | `billing_pkg.issue_invoice` | Asignar consecutivo, registrar factura/detalle y `payment.approved` atómicamente. |

El código/documentación actual contiene nombres españoles como `dbo.reservar_stand`,
`pkg_facturacion.emitir_factura`, `ordenes_pago`, `usuarios` y colecciones `dispositivos`; no se
deben renombrar fuera de migraciones coordinadas.
Las propuestas de nombres ingleses de esta página son objetivo para el siguiente contrato o
migración, no evidencia de que los objetos nuevos ya existan. Consultar [DECISIONES.md](DECISIONES.md)
y [CONTRATOS-API.md](CONTRATOS-API.md) antes de modificar el esquema.
