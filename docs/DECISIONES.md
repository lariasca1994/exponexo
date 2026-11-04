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
| 011 | Costo cero y escala a cero | Aceptada | Solo planes gratuitos y recursos que escalan a cero; si un recurso no tiene opción gratuita, no se usa. Pantalla de espera mientras despiertan los servicios. |
| 012 | Identificadores técnicos en inglés; experiencia y documentación en español | Aceptada | Nombres de símbolos, tablas, columnas, rutas y propiedades JSON nuevos o versionados usan inglés. |
| 013 | UUID v7 generado por la aplicación | Aceptada | Representación nativa por motor; no se reescriben identificadores históricos. |
| 014 | Cuerpos JSON `snake_case` en todos los servicios | Aceptada | Norma global, incluida Mesa de ayuda; el estado actual no está alineado en todos los servicios. |
| 015 | Tokens de acceso y refresco en memoria dentro del portal | Aceptada | Evita exposición en `localStorage`/`sessionStorage` ante XSS y simplifica el flujo CORS entre dominios distintos (Vercel, Azure, Cloud Run). |
| 016 | Token JWT de servicio (RS256) para rutas internas | Aceptada | La ruta legada usa `/v1/interno/...`; el objetivo inglés es `/v1/internal/...`, con migración compatible. |
| 017 | GHCR como registro objetivo para imágenes de servicios en Azure | Aceptada | Evita mantener un ACR dedicado cuando GHCR cabe en las cuotas aplicables; la autenticación de descarga en Azure sigue siendo un requisito previo. |
| 018 | Eventos por un tema SNS con una cola SQS por función | Aceptada | Cada evento llega a todas las funciones que lo necesitan; cada una reintenta y aparta sus fallas por separado. |
| 019 | Configuración en ejecución con los secretos de cada plataforma | Aceptada | Sin servicios de secretos con costo; los workflows la entregan en cada despliegue y los servicios no arrancan si falta. |

---

## Detalle de decisiones (ADR-012 a ADR-017)

### ADR-012: Idioma del código e identificadores
- **Estado:** Aceptada
- **Contexto:** El proyecto combina múltiples lenguajes (Python, Java, C#, TypeScript, SQL) cuyas palabras reservadas, librerías estándar y convenciones de la industria están en inglés, mientras que el dominio funcional y los usuarios hablan español.
- **Opciones:**
  1. Mantener todos los nombres técnicos en español.
  2. Usar inglés para los identificadores técnicos y español para la documentación y la experiencia visible a las personas.
- **Decisión:** Los nombres de código, tablas, columnas, rutas, tipos de evento y propiedades/campos JSON son **en inglés**. Los nombres de dominio visibles, textos de interfaz, errores para personas y documentación narrativa permanecen en español. Los valores de configuración y nombres de variables de entorno ya publicados se conservan literalmente; no se inventan ni se renombran por anticipado.
- **Consecuencias:** Evita mezclar idiomas en contratos y esquemas nuevos. Esta norma es el objetivo de diseño, no una afirmación de que la implementación actual ya esté alineada. Los identificadores existentes se preservan hasta una migración coordinada y compatible.

### ADR-013: Identificadores primarios con UUID
- **Estado:** Aceptada
- **Contexto:** Las entidades (usuarios, reservas, órdenes de pago, entradas, citas) se referencian en URLs de la API y viajan en mensajes de eventos entre servicios con bases de datos distintas (SQL Server, Oracle y MongoDB).
- **Opciones:**
  1. Entero autoincremental generado por la base.
  2. UUID v7 generado en la aplicación antes de persistir o publicar el evento.
- **Decisión:** Generar **UUID v7 en la aplicación** para nuevos identificadores primarios y referencias UUID. SQL Server los almacena como `uniqueidentifier`; Oracle, como `RAW(16)`; MongoDB, cuando un UUID se almacene como UUID BSON, usa `BinData` subtype 4. Los consecutivos de negocio (por ejemplo, el número legible de factura) siguen siendo distintos de la llave UUID y se asignan según su propia regla.
- **Consecuencias:** La generación no depende de la base y los UUID v7 son ordenables aproximadamente por tiempo. Los identificadores históricos, incluso si son UUID v4 o cadenas, **no se regeneran ni convierten solo para cambiar de versión**. Toda conversión futura debe preservar el valor lógico, referencias, índices, claves foráneas, consumidores y posibilidad de reversa.

### ADR-014: Convención `snake_case` para JSON en todas las APIs
- **Estado:** Aceptada
- **Contexto:** El portal consume tres backends escritos en distintos stacks (FastAPI usa `snake_case` por defecto; Spring Boot y ASP.NET Core usan `camelCase` por defecto).
- **Opciones:**
  1. `snake_case` en todos los servicios.
  2. `camelCase` en todos los servicios.
- **Decisión:** Estandarizar todos los cuerpos y propiedades JSON de entrada y salida en **inglés `snake_case`**, globalmente y en todos los servicios, incluida Mesa de ayuda. La regla cubre respuestas de error y cuerpos de eventos; no cambia el nombre de cabeceras HTTP que ya tienen su propia convención.
- **Consecuencias:** FastAPI requiere que los nombres de campos de sus modelos se migren a inglés; Spring Boot ya declara una estrategia `SNAKE_CASE`, mientras que la configuración actual de ASP.NET Core no registra una política global snake_case. La aceptación de esta ADR no significa que todos los contratos existentes hayan completado esa transición.

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
- **Contexto:** El repartidor de eventos (`servicios/eventos`) y el servicio de pagos necesitan invocar rutas internas que nunca deben ser accesibles con el token de un usuario final. La ruta que aparece en el código/documentación actual es `/v1/interno/...`; ADR-012 establece `/v1/internal/...` como nombre objetivo en inglés.
- **Opciones:**
  1. Secreto compartido estático en cabecera.
  2. Token JWT firmado con RS256 por identidad (o emitido mediante credencial de servicio `INTERNO_SECRETO`) con claim de rol/alcance interno, verificado con el mismo JWKS.
- **Decisión:** Proteger las rutas internas objetivo `/v1/internal/...` exigiendo un **JWT RS256 de servicio** (con `role = "service"` / `aud = "exponexo"`), rechazando cualquier token de persona. La ruta legada se conserva como alias durante la migración coordinada y no se retira hasta migrar todos sus clientes.
- **Consecuencias:** Todos los servicios usan un único mecanismo de verificación criptográfica asimétrica (JWKS RS256) tanto para rutas públicas protegidas como para rutas internas.

### ADR-017: Registro de contenedores para servicios desplegados en Azure
- **Estado:** Aceptada
- **Contexto:** Azure Container Registry (ACR) no tiene plan gratuito, lo que rompe el principio de costo cero (ADR-011). GitHub Container Registry (GHCR) aloja las imágenes junto al repositorio dentro del plan gratuito de GitHub.
- **Opciones:**
  1. Mantener ACR (descartada: tiene costo).
  2. Usar GHCR y dar a Azure Container Apps acceso de lectura al paquete.
- **Decisión:** Identidad y Mesa de ayuda publican sus imágenes en GHCR y Azure Container Apps las descarga desde ahí. Pagos usa Google Artifact Registry porque Cloud Run lo requiere, siempre dentro de su capa gratuita. Ambos registros conservan solo las imágenes recientes mediante limpieza automática.
- **Consecuencias:** Ningún registro de contenedores genera cargos. A cambio, la Container App necesita una credencial de solo lectura para GHCR (o un paquete público), administrada fuera del código, y las imágenes antiguas deben depurarse para no salir de la capa gratuita.

### ADR-018: Eventos por un tema SNS con una cola SQS por función
- **Estado:** Aceptada
- **Contexto:** El repartidor y los avisos necesitan recibir los mismos eventos. Si dos funciones leen una misma cola SQS, se reparten los mensajes en vez de recibirlos ambas.
- **Opciones:**
  1. Una cola compartida (descartada: cada evento llega a una sola función).
  2. Que cada servicio publique en varias colas (acopla a los productores con los consumidores).
  3. Un tema SNS que reparte a una cola por función.
- **Decisión:** Los servicios publican su bandeja de salida en el tema `exponexo-eventos`; el tema entrega cada mensaje, tal cual, a la cola de cada función, y cada cola tiene su cola de errores tras 5 intentos.
- **Consecuencias:** Agregar un consumidor nuevo no toca a los productores. Todo cabe en la capa gratuita permanente de SNS, SQS y Lambda. Como identidad, pagos y mesa de ayuda corren fuera de AWS, publican con un usuario que solo tiene permiso `sns:Publish` sobre ese tema.

### ADR-019: Configuración en ejecución con los secretos de cada plataforma
- **Estado:** Aceptada
- **Contexto:** Los servicios necesitan credenciales de bases, correo y firmas en producción, sin guardarlas en el código ni pagar por un servicio de secretos.
- **Opciones:**
  1. Servicios dedicados de secretos (Key Vault, Secret Manager): cobran por versión u operación.
  2. Secretos de la propia plataforma: Container Apps, variables cifradas de la revisión en Cloud Run y de la función en Lambda.
- **Decisión:** La fuente única es el entorno `produccion` de GitHub; en cada despliegue, un script entrega a cada nube solo lo que su servicio necesita. El wallet de Oracle viaja como zip en base64 y pagos lo descomprime al arrancar.
- **Consecuencias:** Costo cero y una sola fuente de verdad. Rotar un secreto es cambiarlo en GitHub y volver a desplegar. Cada servicio valida su configuración al arrancar y se niega a funcionar con valores de desarrollo.

