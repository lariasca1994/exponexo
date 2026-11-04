# Contratos de API de ExpoNexo

Rutas reales de cada servicio. Cada uno publica además su OpenAPI (FastAPI en `/docs`); ante
cualquier duda, manda el código.

## Convenciones

- Prefijo `/v1`; rutas, parámetros y propiedades JSON en español y en `snake_case`
  (ADR-012 y ADR-014). Las cabeceras HTTP conservan su forma estándar: `Authorization`,
  `Idempotency-Key` y `X-Correlation-Id`.
- Autenticación con `Authorization: Bearer <token>`: identidad emite JWT RS256 y publica sus llaves
  en `/.well-known/jwks.json`; pagos y mesa de ayuda verifican la firma, el emisor, la audiencia y
  el vencimiento (ADR-008).
- Roles: `visitante`, `expositor`, `personal` y `administrador`. Las rutas `/v1/interno/...` solo
  aceptan el token de servicio (ADR-016).
- Errores con `application/problem+json` (RFC 9457: `type`, `title`, `status`, `detail`).
- `GET /salud` sin autenticación en los tres servicios, para la comprobación de despliegue.

## 1. Identidad, reservas y agenda (`:8001`)

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/v1/cuentas` | Registrar cuenta |
| POST | `/v1/cuentas/confirmar-correo` | Confirmar el correo con el código |
| POST | `/v1/cuentas/recuperar` | Recuperar la contraseña |
| POST | `/v1/sesion/ingreso` | Ingresar con correo y contraseña (primer paso) |
| POST | `/v1/sesion/codigo-correo` | Pedir el código por correo |
| POST | `/v1/sesion/segundo-paso` | Completar la verificación en dos pasos |
| POST | `/v1/sesion/llave/opciones` · `/v1/sesion/llave` | Ingresar con llave de acceso (WebAuthn) |
| POST | `/v1/sesion/refrescar` · `/v1/sesion/salir` | Renovar o cerrar la sesión |
| POST | `/v1/sesion/servicio` | Token de servicio para el repartidor y pagos |
| GET | `/v1/perfil/seguridad` | Estado de MFA y llaves |
| POST | `/v1/perfil/mfa/app` · `/v1/perfil/mfa/app/confirmar` | Activar la app autenticadora |
| POST | `/v1/perfil/mfa/correo` | Activar el código por correo |
| PUT | `/v1/perfil/mfa/preferido` | Elegir el método preferido |
| POST | `/v1/perfil/codigos-respaldo` | Generar códigos de respaldo |
| POST | `/v1/perfil/llaves/opciones` · `/v1/perfil/llaves` | Registrar una llave de acceso |
| GET | `/v1/eventos` · `/v1/eventos/{slug}` · `/v1/eventos/{id}/stands` | Catálogo público |
| GET | `/v1/pabellones` | Pabellones y su plano |
| POST/PUT | `/v1/admin/eventos[/{id}]` · `/v1/admin/pabellones[/{id}]` · `/v1/admin/stands[/{id}]` | Administrar el catálogo |
| GET | `/v1/admin/resumen` | Tablero del administrador |
| POST | `/v1/empresas` · GET `/v1/empresas/mia` | Empresa del expositor |
| POST | `/v1/reservas` · GET `/v1/reservas/mias` · DELETE `/v1/reservas/{id}` | Reservar stand (procedimiento `reservar_stand`) |
| POST | `/v1/eventos/{id}/entradas` · GET `/v1/mis-entradas` | Comprar y ver entradas |
| POST | `/v1/entradas/validar-qr` | Validar el QR en la puerta (personal) |
| PUT | `/v1/eventos/{id}/mi-disponibilidad` | Disponibilidad para la agenda de negocios |
| GET | `/v1/eventos/{id}/expositores` · `/v1/eventos/{id}/expositores/{exp}/huecos` | Buscar con quién reunirse |
| POST | `/v1/citas` · `/v1/citas/{id}/responder` · GET `/v1/mis-citas` | Citas de negocios |
| POST | `/v1/pabellones/{id}/salas` | Salas de reunión (administrador) |
| POST | `/v1/imagenes/subir` | Subir imágenes a Cloudinary |

Rutas internas (solo token de servicio): `GET /v1/interno/reservas/{id}`,
`POST /v1/interno/reservas/{id}/pagada`, `POST /v1/interno/reservas/{id}/reembolsar`,
`POST /v1/interno/reservas/vencer`, `GET /v1/interno/entradas/{id}`,
`POST /v1/interno/entradas/{id}/activar`, `POST /v1/interno/entradas/{id}/cancelar` y
`POST /v1/interno/bandeja/publicar`.

## 2. Pagos y facturación (`:8002`)

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/v1/ordenes` | Crear la orden de pago de una reserva o entrada |
| GET | `/v1/ordenes/{id}` | Consultar la orden |
| POST | `/v1/ordenes/{id}/qr` | Generar el cobro con QR firmado |
| POST | `/v1/ordenes/{id}/pagar` | Pagar (emite la factura con `pkg_facturacion`) |
| POST | `/v1/ordenes/{id}/reembolsos` | Reembolsar |
| GET | `/v1/facturas/mias` · `/v1/facturas/{numero}` | Facturas del usuario |
| GET | `/v1/admin/resumen` | Tablero del administrador |

La salud de despliegue también responde en `/actuator/health`.

## 3. Mesa de ayuda y monitoreo (`:8003`)

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/v1/tickets` · GET `/v1/tickets` · GET `/v1/tickets/{id}` | Crear y consultar tickets |
| POST | `/v1/tickets/{id}/tomar` · `/escalar` · `/resolver` | Atender un ticket (SLA) |
| POST | `/v1/dispositivos/enrolar` | Enrolar un dispositivo con el código de enrolamiento |
| POST | `/v1/dispositivos/{id}/lecturas` | Reportar lecturas |
| GET | `/v1/dispositivos` | Estado de los dispositivos |
| POST | `/v1/interno/monitoreo/ejecutar` | Revisar dispositivos sin reporte y SLA vencidos (servicio) |
| GET | `/v1/admin/resumen` | Tablero del administrador |

Los cambios que interesan a otros servicios viajan como eventos: ver [EVENTOS.md](EVENTOS.md).
