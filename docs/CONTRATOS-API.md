# Contratos de API de ExpoNexo

Este documento define la **norma objetivo** para contratos nuevos o migrados. No representa una
descripción exacta de todas las rutas desplegadas hoy: las APIs actuales todavía contienen rutas
y campos en español y no hay una política de compatibilidad común implementada. Comprueba el
OpenAPI y el código de cada servicio antes de depender de una ruta.

## Convenciones objetivo

- Prefijo `/v1`; identificadores de ruta, nombres de parámetros y segmentos en inglés.
- Cuerpos JSON en inglés `snake_case` para solicitudes, respuestas, errores y datos de eventos,
  incluidos los de Mesa de ayuda. Los nombres de cabecera HTTP conservan su forma definida, por
  ejemplo `Authorization`, `Idempotency-Key` y `X-Correlation-Id`.
- Errores con `application/problem+json` y RFC 9457 (`type`, `title`, `status`, `detail`,
  `instance`); cualquier extensión, como `correlation_id`, también va en `snake_case`.
- Listas paginadas: `page`, `page_size`, `total`.
- Rutas internas bajo `/v1/internal/...`, autorizadas solo para servicios.
- `GET /health` sin autenticación para comprobación de salud. La ruta actual `/salud` no cambia
  hasta que se despliegue una ruta compatible.

Roles objetivo: `public`, `visitor`, `exhibitor`, `staff`, `admin`, `internal`. Las etiquetas
visibles a las personas pueden seguir en español.

## Estado y política de compatibilidad

**Estado observado en el repositorio:** Identidad y Reservas declara rutas como `/v1/eventos`,
`/v1/reservas` y `/v1/sesion/ingreso`, y sus modelos Pydantic exponen nombres como `correo`,
`token_acceso` y `creado_en`. Pagos conserva rutas como `/v1/ordenes` y `/v1/facturas`, aunque
`application.properties` ya configura la serialización Jackson `SNAKE_CASE`. Mesa de ayuda
implementa, entre otras, `/v1/tickets/{id}/tomar` y `/v1/dispositivos/{id}/lecturas`; no registra
una política JSON global snake_case. Por tanto, ni las rutas inglesas ni la regla uniforme de
campos están desplegadas en todos los servicios.

La tabla de abajo es el contrato objetivo. En el periodo de migración, la ruta y los campos
anteriores se consideran **contrato legado**. No se elimina ni reutiliza silenciosamente una ruta:

1. Acordar consumidores, ventana de transición, propietario y versión del contrato; publicar el
   nuevo OpenAPI antes de cambiar clientes.
2. Desplegar el proveedor con compatibilidad explícita (alias/adaptador o versión de ruta) que
   acepte el contrato legado y el objetivo sin ambigüedad. Mantener el comportamiento,
   autorizaciones, códigos HTTP e idempotencia.
3. Migrar portal, servicios consumidores y pruebas de contrato coordinadamente. Medir llamadas
   al contrato legado y anunciar su retiro con fecha acordada.
4. Retirar el alias solo después de comprobar que no quedan consumidores. No traducir valores
   libres, slugs, códigos de negocio, tokens o contenido de usuarios como si fueran nombres de
   propiedad.

No se convierten recursos ni registros solo para cambiar el idioma de sus identificadores. Si una
ruta usa un identificador histórico, ese valor y sus referencias permanecen válidos. Para cambios
de forma JSON, conservar la representación antigua mientras convivan los dos contratos; rechazar
campos contradictorios y documentar precedencia/errores.

## 1. Identidad, reservas y agenda (`:8001`)

### Cuentas y sesiones

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| POST | `/v1/accounts` | public | Crear cuenta. |
| POST | `/v1/accounts/confirm-email` | public | Confirmar correo. |
| POST | `/v1/sessions/login` | public | Validar credenciales y emitir pase de segundo paso. |
| POST | `/v1/sessions/mfa` | public | Validar el segundo paso y emitir tokens. |
| POST | `/v1/sessions/email-code` | public | Enviar el código del segundo paso. |
| POST | `/v1/sessions/refresh` | public | Renovar acceso. |
| POST | `/v1/sessions/logout` | visitor, exhibitor, staff, admin | Revocar el token de refresco. |
| POST | `/v1/accounts/password-recovery` | public | Recuperar contraseña. |
| GET | `/.well-known/jwks.json` | public | Publicar claves para verificar JWT. |

### Perfil y passkeys

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| GET | `/v1/profile/security` | visitor, exhibitor, staff, admin | Ver métodos MFA, llaves y sesiones. |
| POST | `/v1/profile/mfa/authenticator` | usuario autenticado | Iniciar configuración de autenticador. |
| POST | `/v1/profile/mfa/authenticator/confirm` | usuario autenticado | Confirmar autenticador. |
| POST | `/v1/profile/mfa/email` | usuario autenticado | Habilitar código por correo. |
| PUT | `/v1/profile/mfa/preferred` | usuario autenticado | Cambiar método preferido. |
| POST | `/v1/profile/backup-codes` | usuario autenticado | Renovar códigos de respaldo. |
| POST | `/v1/profile/passkeys/options` | usuario autenticado | Crear opciones de registro. |
| POST | `/v1/profile/passkeys` | usuario autenticado | Registrar passkey. |
| POST | `/v1/sessions/passkeys/options` | public | Crear opciones de ingreso con passkey. |
| POST | `/v1/sessions/passkeys` | public | Verificar passkey e iniciar sesión. |

### Catálogo y reservas

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| GET | `/v1/events` | public | Listar eventos publicados. |
| GET | `/v1/events/{slug}` | public | Consultar evento. |
| GET | `/v1/events/{event_id}/booths` | public | Consultar stands y disponibilidad. |
| POST, PUT | `/v1/admin/events`, `/v1/admin/halls`, `/v1/admin/booths` | admin | Administrar catálogo. |
| POST | `/v1/reservations` | exhibitor | Reservar stand; requiere `Idempotency-Key`. |
| GET | `/v1/reservations/mine` | exhibitor | Consultar reservas propias. |
| DELETE | `/v1/reservations/{reservation_id}` | exhibitor | Cancelar reserva pendiente. |
| GET | `/v1/internal/reservations/{reservation_id}` | internal | Consultar monto y estado para pagos. |
| POST | `/v1/internal/reservations/{reservation_id}/paid` | internal | Registrar pago aprobado. |
| POST | `/v1/internal/reservations/{reservation_id}/refund` | internal | Procesar reembolso asociado. |

### Entradas y agenda

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| POST | `/v1/admissions` | visitor | Comprar entrada. |
| GET | `/v1/admissions/mine` | visitor | Consultar entradas propias. |
| POST | `/v1/internal/admissions/{admission_id}/activate` | internal | Activar entrada pagada. |
| PUT | `/v1/events/{event_id}/availability` | exhibitor | Definir franjas de citas. |
| GET | `/v1/exhibitors/{exhibitor_id}/availability` | visitor, exhibitor | Consultar franjas libres. |
| POST | `/v1/appointments` | visitor, exhibitor | Proponer cita. |
| PUT | `/v1/appointments/{appointment_id}/accept` | visitor, exhibitor | Aceptar cita. |
| PUT | `/v1/appointments/{appointment_id}/reject` | visitor, exhibitor | Rechazar cita. |
| GET | `/v1/appointments/mine` | visitor, exhibitor | Consultar agenda propia. |
| GET | `/v1/admin/summary` | admin | Consultar resumen de operación. |

La ruta actual de entradas está en español; su migración a `admissions` debe incluir portal,
productor, consumidor y pruebas de contrato.

## 2. Pagos y facturación (`:8002`)

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| POST | `/v1/orders` | exhibitor, visitor | Crear orden idempotente. |
| GET | `/v1/orders/{order_id}` | propietario | Consultar orden. |
| POST | `/v1/orders/{order_id}/qr` | propietario | Generar cobro QR. |
| POST | `/v1/orders/{order_id}/pay` | propietario / integración de pago | Confirmar el pago simulado actual. |
| GET | `/v1/invoices/mine` | exhibitor, visitor | Listar facturas propias. |
| GET | `/v1/invoices/{invoice_number}` | propietario, admin | Consultar factura. |
| POST | `/v1/orders/{order_id}/refunds` | admin | Registrar reembolso. |
| GET | `/v1/admin/summary` | admin | Consultar ingresos por evento y origen. |

## 3. Mesa de ayuda y monitoreo (`:8003`)

| Método | Ruta objetivo | Rol | Propósito |
|---|---|---|---|
| POST | `/v1/tickets` | exhibitor, staff | Abrir ticket de soporte. |
| GET | `/v1/tickets` | staff, admin | Listar tickets con filtros. |
| GET | `/v1/tickets/mine` | exhibitor | Consultar tickets propios. |
| GET | `/v1/tickets/{ticket_id}` | exhibitor, staff, admin | Consultar detalle e historial. |
| POST | `/v1/tickets/{ticket_id}/take` | staff | Tomar/asignar ticket. |
| POST | `/v1/tickets/{ticket_id}/escalate` | staff | Escalar nivel. |
| POST | `/v1/tickets/{ticket_id}/resolve` | staff | Resolver ticket. |
| POST | `/v1/devices/register` | device | Enrolar dispositivo autorizado. |
| POST | `/v1/devices/{device_id}/readings` | device | Enviar lectura. |
| GET | `/v1/devices` | staff, admin | Consultar dispositivos. |
| POST | `/v1/internal/monitoring/run` | internal | Ejecutar monitoreo autorizado. |
| GET | `/v1/admin/summary` | admin | Consultar tickets y SLA. |

## 4. Pagos y eventos internos

Las rutas de pago y las rutas internas se especifican con el nombre inglés del contrato, pero las
integraciones existentes actualmente contienen rutas españolas. El cambio se despliega en ambos
extremos con alias temporal y pruebas de contrato; el servicio consumidor no debe cambiarse antes
de que el proveedor admita la ruta nueva.

Las funciones de eventos no exponen API pública. Ver [EVENTOS.md](EVENTOS.md) para los nombres
objetivo, el mapeo de eventos actuales y el procedimiento de versionado.
