# Registro de decisiones de arquitectura

Cada decisión importante se anota aquí en formato **ADR** (Architecture Decision Record): así,
dentro de seis meses (o en una entrevista) puedes explicar por qué está hecho así. Investiga
«Architecture Decision Records Michael Nygard».

**Formato de cada decisión:**

| Campo | Qué escribir |
|---|---|
| Número y título | «ADR-007: Procedimientos almacenados para reservas» |
| Estado | Propuesta, aceptada, reemplazada por ADR-XXX |
| Contexto | Qué problema había y qué restricciones |
| Opciones | Las alternativas que consideraste |
| Decisión | La que elegiste |
| Consecuencias | Qué ganas y qué pierdes |

---

## Resumen de decisiones

| ADR | Decisión | Estado | Puntos para tu contexto y consecuencias |
|---|---|---|---|
| 001 | Monorepo con un servicio por carpeta | Aceptada | Un solo lugar para la documentación y los contratos; despliegue independiente por carpeta. |
| 002 | Cuatro servicios y una base por servicio | Aceptada | Separación por dominio de negocio; ningún servicio lee la base de otro. |
| 003 | FastAPI + SQL Server para identidad, reservas y agenda | Aceptada | Reglas transaccionales con cupos y fechas; muy común en empresas. |
| 004 | Spring Boot + Oracle para pagos y facturación | Aceptada | Estándar en banca y facturación; consecutivos y transacciones robustas. |
| 005 | ASP.NET Core + MongoDB para mesa de ayuda y monitoreo | Aceptada | Tickets con historial embebido y lecturas de dispositivos de alto volumen. |
| 006 | Cola de mensajes con bandeja de salida | Aceptada | Desacople y entrega confiable entre servicios. |
| 007 | Procedimientos almacenados para las reglas atómicas (reservas y facturación) | Aceptada | Consistencia garantizada por la base; igual que el resto del portafolio. |
| 008 | Identidad emite JWT RS256 y publica JWKS | Aceptada | Los demás servicios verifican sin conocer la clave privada. |
| 009 | Verificación en dos pasos obligatoria y llaves de acceso | Aceptada | Seguridad del ingreso a la altura de una plataforma real. |
| 010 | Portal React + TypeScript como PWA | Aceptada | Una interfaz para todos los roles, instalable. |
| 011 | Costo cero y escala a cero | Aceptada | Planes gratuitos; pantalla de espera mientras despiertan los servicios. |
| 012 | Código e identificadores en inglés; documentación y mensajes al usuario en español | Aceptada | Sigue el estándar internacional en código (Python, Java, C#, TypeScript) manteniendo la experiencia de usuario y documentación en español. |
| 013 | Identificadores primarios UUID en todas las tablas relacionales | Aceptada | Evita enumeración de recursos en URLs públicas y facilita la generación de IDs antes de persistir o en eventos. |
| 014 | Cuerpos JSON en `snake_case` en todos los servicios | Aceptada | Consistencia uniforme entre FastAPI, Spring Boot y ASP.NET Core; mapeo directo con esquemas y base de datos. |
| 015 | Tokens de acceso y refresco en memoria dentro del portal | Aceptada | Evita exposición en `localStorage`/`sessionStorage` ante XSS y simplifica el flujo CORS entre dominios distintos (Vercel, Azure, Cloud Run). |
| 016 | Token JWT de servicio (RS256) para rutas internas `/v1/interno/...` | Aceptada | Reutiliza la infraestructura JWKS de identidad diferenciando tokens de persona (`sub` usuario) de tokens de servicio (`scope`/`role: internal_service`). |

---

## Detalle de decisiones tomadas en Fase 0 (ADR-012 a ADR-016)

### ADR-012: Idioma del código e identificadores
- **Estado:** Aceptada
- **Contexto:** El proyecto combina múltiples lenguajes (Python, Java, C#, TypeScript, SQL) cuyas palabras reservadas, librerías estándar y convenciones de la industria están en inglés, mientras que el dominio funcional y los usuarios hablan español.
- **Opciones:**
  1. Todo en español (código, tablas y documentación).
  2. Código e identificadores técnicos en inglés; documentación, comentarios de dominio y mensajes visibles al usuario en español.
- **Decisión:** Escribir el código fuente, clases, funciones y variables en **inglés**, manteniendo la documentación y los textos de interfaz/errores al usuario en **español** (y respetando los contratos de rutas/tablas del diseño cuando aplique).
- **Consecuencias:** Se evita el «Spanglish» con palabras reservadas y frameworks (`class User`, `async def verify_mfa`), facilitando la lectura técnica internacional.

### ADR-013: Identificadores primarios con UUID
- **Estado:** Aceptada
- **Contexto:** Las entidades (usuarios, reservas, órdenes de pago, entradas, citas) se referencian en URLs de la API y viajan en mensajes de eventos entre servicios con bases de datos distintas (SQL Server, Oracle y MongoDB).
- **Opciones:**
  1. Entero autoincremental (`IDENTITY` / `SEQUENCE`).
  2. `UUID` (v4/v7) en todas las tablas (`UNIQUEIDENTIFIER` en SQL Server, `RAW(16)` o `VARCHAR2(36)` en Oracle).
- **Decisión:** Usar **UUID** como llave primaria en todas las tablas relacionales (además del número consecutivo de negocio en `facturas` mediante secuencia en Oracle).
- **Consecuencias:** Los identificadores no son predecibles ni enumerables desde fuera, y pueden generarse en aplicación o en base de datos sin colisiones entre microservicios.

### ADR-014: Convención `snake_case` para JSON en todas las APIs
- **Estado:** Aceptada
- **Contexto:** El portal consume tres backends escritos en distintos stacks (FastAPI usa `snake_case` por defecto; Spring Boot y ASP.NET Core usan `camelCase` por defecto).
- **Opciones:**
  1. `snake_case` en todos los servicios.
  2. `camelCase` en todos los servicios.
- **Decisión:** Estandarizar todos los contratos JSON de entrada y salida en **`snake_case`**.
- **Consecuencias:** FastAPI no requiere alias adicionales; en Spring Boot (`spring.jackson.property-naming-strategy=SNAKE_CASE`) y ASP.NET Core (`JsonNamingPolicy.SnakeCaseLower`) se configura globalmente en una sola línea.

### ADR-015: Almacenamiento de tokens en memoria en el portal
- **Estado:** Aceptada
- **Contexto:** Guardar tokens en `localStorage` los expone a cualquier script en caso de XSS, mientras que las cookies `HttpOnly` entre dominios distintos (`vercel.app`, `azurecontainerapps.io`, `run.app`) sufren bloqueos por políticas de cookies de terceros en navegadores modernos.
- **Opciones:**
  1. `localStorage`.
  2. Access token en memoria + Refresh token en cookie `HttpOnly`.
  3. Ambos tokens (acceso y refresco) gestionados en memoria de la aplicación.
- **Decisión:** Mantener **ambos tokens en memoria** dentro del estado de sesión del portal (con rotación y revocación en la tabla `sesiones` del servicio de identidad).
- **Consecuencias:** Ningún token queda persistido en almacenamiento accesible por disco/DOM, y las llamadas CORS entre Vercel y los tres servicios en distintas nubes funcionan sin restricciones de cookies cross-site.

### ADR-016: Autenticación entre servicios con JWT de servicio (RS256)
- **Estado:** Aceptada
- **Contexto:** El repartidor de eventos (`servicios/eventos`) y el servicio de pagos necesitan invocar rutas internas (`/v1/interno/...`) que nunca deben ser accesibles con el token de un usuario final.
- **Opciones:**
  1. Secreto compartido estático en cabecera.
  2. Token JWT firmado con RS256 por identidad (o emitido mediante credencial de servicio `INTERNO_SECRETO`) con claim de rol/alcance interno, verificado con el mismo JWKS.
- **Decisión:** Proteger `/v1/interno/...` exigiendo un **JWT RS256 de servicio** (con `role = "service"` / `aud = "exponexo"`), rechazando cualquier token de persona (`visitante`, `expositor`, `personal`, `administrador`).
- **Consecuencias:** Todos los servicios usan un único mecanismo de verificación criptográfica asimétrica (JWKS RS256) tanto para rutas públicas protegidas como para rutas internas.
