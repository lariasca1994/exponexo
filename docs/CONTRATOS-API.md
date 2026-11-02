# Contratos de API de ExpoNexo

Cada servicio publica su contrato **OpenAPI** (FastAPI lo genera solo; en Spring Boot investiga
«springdoc-openapi»; en ASP.NET Core, «Microsoft.AspNetCore.OpenApi»). Este documento es la lista
de lo que debe exponer cada uno: úsala como guía de diseño y verifica después que el OpenAPI real
coincida (pruebas de contrato, fase 8).

**Convenciones para todos:**

- Prefijo de versión: `/v1/...`.
- JSON en `camelCase` o `snake_case`, pero el mismo en todos (decídelo y anótalo en
  [DECISIONES.md](DECISIONES.md)).
- Errores con un formato común. Investiga **RFC 9457 «Problem Details»** (`type`, `title`,
  `status`, `detail`).
- Paginación en listas (`pagina`, `tamano`, total).
- Toda ruta protegida exige `Authorization: Bearer <token>`.
- Cabecera `X-Correlation-Id` en peticiones y respuestas.
- `GET /salud` en cada servicio, sin autenticación, para monitoreo.
- Rutas **internas** (las llama el repartidor de eventos) bajo `/v1/interno/...`, solo con token de
  servicio.

Rol: **P** = público · **V** = visitante · **E** = expositor · **S** = personal · **A** =
administrador · **I** = interno (servicio).

---

## 1. Identidad, reservas y agenda (`:8001`)

### Cuenta e ingreso

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | /v1/cuentas | P | Registro (correo, nombre, contraseña, rol solicitado `visitante` o `expositor`). |
| POST | /v1/cuentas/confirmar-correo | P | Confirma el correo con el código enviado. |
| POST | /v1/sesion/ingreso | P | Paso 1: correo y contraseña → devuelve un «pase» de segundo paso y los métodos disponibles. |
| POST | /v1/sesion/segundo-paso | P (con pase) | Paso 2: código de la app, del correo o de respaldo → tokens de acceso y refresco. |
| POST | /v1/sesion/codigo-correo | P (con pase) | Envía el código por correo. |
| POST | /v1/sesion/refrescar | P (con refresco) | Nuevo token de acceso. |
| POST | /v1/sesion/salir | V E S A | Revoca el refresco actual. |
| POST | /v1/cuentas/recuperar | P | Solicitar y confirmar el restablecimiento de contraseña. |
| GET | /.well-known/jwks.json | P | Clave pública para que los demás servicios verifiquen tokens. |

### Seguridad del perfil

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| GET | /v1/perfil/seguridad | V E S A | Métodos activos, preferido, llaves y sesiones. |
| POST | /v1/perfil/mfa/app | V E S A | Inicia la app autenticadora (devuelve el QR y la clave). |
| POST | /v1/perfil/mfa/app/confirmar | V E S A | Activa la app con su primer código. |
| POST | /v1/perfil/mfa/correo | V E S A | Activa el código por correo. |
| PUT | /v1/perfil/mfa/preferido | V E S A | Elige el método por defecto. |
| POST | /v1/perfil/codigos-respaldo | V E S A | Genera códigos de respaldo nuevos. |
| POST | /v1/perfil/llaves/opciones | V E S A | Opciones para registrar una llave de acceso. |
| POST | /v1/perfil/llaves | V E S A | Guarda la llave registrada. |
| POST | /v1/sesion/llave/opciones, /v1/sesion/llave | P | Ingreso con llave de acceso. |

### Catálogo y reservas

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| GET | /v1/eventos | P | Eventos publicados. |
| GET | /v1/eventos/{slug} | P | Detalle del evento. |
| GET | /v1/eventos/{id}/stands | P | Stands con su estado (disponible, reservado, pagado). |
| POST, PUT | /v1/admin/eventos, /v1/admin/pabellones, /v1/admin/stands | A | Administración del catálogo. |
| POST | /v1/reservas | E | Reserva un stand (llama al procedimiento `reservar_stand`). Exige `Idempotency-Key`. |
| GET | /v1/reservas/mias | E | Reservas del expositor. |
| DELETE | /v1/reservas/{id} | E | Cancela una reserva pendiente. |
| GET | /v1/interno/reservas/{id} | I | Monto y estado (lo consulta pagos). |
| POST | /v1/interno/reservas/{id}/pagada | I | Marca la reserva pagada (desde `pago.aprobado`). |

### Entradas y agenda

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | /v1/entradas | V | Compra una entrada (queda pendiente de pago). |
| GET | /v1/entradas/mias | V | Entradas con su QR cuando estén activas. |
| POST | /v1/interno/entradas/{id}/activa | I | Activa la entrada pagada. |
| PUT | /v1/disponibilidad | E | Define franjas disponibles para citas. |
| GET | /v1/expositores/{id}/disponibilidad | V E | Franjas libres. |
| POST | /v1/citas | V E | Propone una cita. |
| PUT | /v1/citas/{id}/aceptar, /rechazar | E V | Responde (aceptar usa `aceptar_cita`). |
| GET | /v1/citas/mias | V E | Agenda propia. |
| GET | /v1/admin/resumen | A | Ocupación, entradas y citas por evento (tablero). |

---

## 2. Pagos y facturación (`:8002`)

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | /v1/ordenes | E V | Crea la orden para una reserva o entrada (con `Idempotency-Key`). El monto lo obtiene del servicio de reservas. |
| GET | /v1/ordenes/{id} | E V | Estado de la orden. |
| POST | /v1/ordenes/{id}/qr | E V | Genera el cobro QR vigente. |
| POST | /v1/ordenes/{id}/pagar | E V | Simula el pago del QR (en la vida real lo confirmaría el banco). |
| GET | /v1/facturas/mias | E V | Facturas propias. |
| GET | /v1/facturas/{numero} | E V A | Detalle de la factura. |
| POST | /v1/ordenes/{id}/reembolsos | A | Registra un reembolso. |
| GET | /v1/admin/resumen | A | Ingresos por evento y por origen (tablero). |

---

## 3. Mesa de ayuda y monitoreo (`:8003`)

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | /v1/tickets | E S | Abre un ticket (prioridad y ubicación). |
| GET | /v1/tickets | S A | Bandeja con filtros (estado, prioridad, nivel). |
| GET | /v1/tickets/mios | E | Tickets propios. |
| GET | /v1/tickets/{codigo} | E S A | Detalle con historial y tiempo restante del SLA. |
| PUT | /v1/tickets/{codigo}/estado | S | Cambia el estado (queda en el historial). |
| PUT | /v1/tickets/{codigo}/asignar | S A | Asigna a una persona del personal. |
| POST | /v1/dispositivos/enrolar | P (con código de enrolamiento) | Registra un kiosco o pantalla. |
| POST | /v1/dispositivos/{codigo}/lecturas | Dispositivo | Envía una lectura. |
| GET | /v1/dispositivos | S A | Estado de todos los dispositivos. |
| GET | /v1/admin/resumen | A | Tickets por estado y cumplimiento de SLA (tablero). |

---

## 4. Funciones de eventos

No exponen API pública. El repartidor consume la cola y llama a las rutas `/v1/interno/...`
correspondientes; avisos consume la cola y envía correos y mensajes. Ver [EVENTOS.md](EVENTOS.md).
