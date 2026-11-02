# Ruta de aprendizaje

Qué estudiar, en qué orden y dónde. Estudia cada bloque **justo antes** de la fase que lo usa: lo
que aprendes y aplicas en la misma semana se queda; lo que estudias meses antes se olvida.

**Cómo estudiar cada tema:**

1. Lee la sección de la documentación oficial indicada (no un video de 3 horas).
2. Haz el ejemplo mínimo de la documentación **en una carpeta aparte**, fuera de ExpoNexo.
3. Explícalo en voz alta o por escrito en tres frases. Si no puedes, vuelve al paso 1.
4. Recién entonces aplícalo en ExpoNexo.

---

## Bloque 0 · Bases (fase 0)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| HTTP | Métodos, códigos de estado (200, 201, 400, 401, 403, 404, 409, 422, 500), cabeceras, CORS | MDN Web Docs: «HTTP overview», «CORS» |
| REST | Recursos, rutas en plural, idempotencia de los métodos | «REST API design best practices» |
| JSON y JSON Schema | Tipos, validación | json-schema.org |
| Git | Ramas, merge, rebase básico, pull requests | git-scm.com/book (capítulos 2 y 3) |
| Microservicios | Ventajas, costos, cuándo no usarlos | microservices.io: «Microservice Architecture pattern», «Database per service» |
| Variables de entorno | Configuración fuera del código | 12factor.net: «III. Config» |

## Bloque 1 · Identidad y portal (fase 1)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Python moderno | Tipado (`typing`), `dataclasses`, entornos virtuales | docs.python.org: «Tutorial», «venv» |
| FastAPI | Rutas, Pydantic, dependencias, `APIRouter`, manejo de errores, documentación automática | fastapi.tiangolo.com: «Tutorial - User Guide» completo |
| SQLAlchemy 2 | Modelos con `Mapped`, sesiones, transacciones | docs.sqlalchemy.org: «ORM Quick Start», «Unified Tutorial» |
| Alembic | Migraciones y autogeneración | alembic.sqlalchemy.org: «Tutorial» |
| SQL Server | Tipos, índices, restricciones, `T-SQL` básico | learn.microsoft.com: «Transact-SQL reference» |
| Contraseñas | Por qué hash lento con sal (Argon2) | OWASP: «Password Storage Cheat Sheet» |
| MFA / TOTP | Cómo una app genera códigos; RFC 6238 | RFC 6238; OWASP: «Multifactor Authentication Cheat Sheet» |
| JWT y JWKS | Firma RS256, `iss`, `aud`, `exp`, rotación de claves | jwt.io: «Introduction»; RFC 7517 (JWK) |
| Sesiones | Tokens de acceso y refresco, revocación | OWASP: «Session Management Cheat Sheet» |
| WebAuthn | Llaves de acceso (passkeys): registro e ingreso | webauthn.guide; passkeys.dev |
| React | Componentes, props, estado, efectos | react.dev: «Learn» completo |
| TypeScript | Tipos, interfaces, genéricos básicos | typescriptlang.org: «Handbook» |
| React Router | Rutas, rutas protegidas | reactrouter.com: «Tutorial» |
| TanStack Query | Caché de peticiones, mutaciones | tanstack.com/query: «Overview», «Quick Start» |
| PWA | Manifiesto, service worker, modo sin conexión | web.dev: «Learn PWA»; vite-pwa-org.netlify.app |

## Bloque 2 · Reservas y procedimientos almacenados (fase 2)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Transacciones | ACID, niveles de aislamiento, bloqueos | learn.microsoft.com: «Transaction locking and row versioning guide» |
| Procedimientos almacenados en T-SQL | Parámetros de entrada y salida, `TRY…CATCH`, `THROW`, `XACT_ABORT` | learn.microsoft.com: «CREATE PROCEDURE» |
| Concurrencia | Condiciones de carrera, índices únicos filtrados, `rowversion` | «filtered index SQL Server», «optimistic concurrency» |
| Control de acceso | RBAC por rol | OWASP: «Authorization Cheat Sheet» |
| Idempotencia en APIs | `Idempotency-Key` | «idempotency key Stripe API» (es el ejemplo clásico) |

## Bloque 3 · Pagos (fase 3)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Java 25 | Records, `Optional`, colecciones, excepciones | dev.java: «Learn» |
| Maven | `pom.xml`, ciclo de vida, wrapper `mvnw` | maven.apache.org: «Maven in 5 Minutes» |
| Spring Boot | Inyección de dependencias, `@RestController`, `@Service`, perfiles | spring.io/guides: «Building a RESTful Web Service», «Accessing Data with JPA» |
| Spring Data JPA | Entidades, repositorios, transacciones (`@Transactional`) | docs.spring.io: «Spring Data JPA reference» |
| Spring Security | Resource Server con JWT y JWKS | docs.spring.io: «OAuth 2.0 Resource Server JWT» |
| Flyway | Migraciones versionadas (`V`) y repetibles (`R`) | documentation.red-gate.com/flyway |
| Oracle y PL/SQL | Tipos, secuencias, paquetes y procedimientos, excepciones | docs.oracle.com: «PL/SQL Language Reference» |
| Wallet de Oracle | Conexión mTLS a Autonomous Database desde Java | docs.oracle.com: «Connect to Autonomous Database using JDBC with wallet» |
| Dinero | `BigDecimal`, redondeo, impuestos | «Java BigDecimal money best practices» |

## Bloque 4 · Eventos (fase 4)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Arquitectura orientada a eventos | Coreografía, eventos vs comandos | microservices.io: «Event-driven architecture», «Saga» |
| Outbox | Publicación confiable | microservices.io: «Transactional outbox» |
| Amazon SQS | Colas estándar, visibilidad, cola de errores | docs.aws.amazon.com: «Amazon SQS Developer Guide» |
| AWS Lambda | Funciones en Python, disparador SQS, empaquetado | docs.aws.amazon.com: «Lambda with Python», «Using Lambda with Amazon SQS» |
| boto3 | Cliente de AWS para Python | boto3.amazonaws.com: «SQS» |
| Brevo | Correo transaccional por API | developers.brevo.com: «Send a transactional email» |
| Telegram | Bots y `sendMessage` | core.telegram.org/bots/api |

## Bloque 5 · Agenda (fase 5)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Fechas y zonas horarias | UTC en la base, conversión al mostrar | «store dates in UTC best practice», `zoneinfo` en Python |
| Solapamiento de intervalos | Condición `inicio_a < fin_b y inicio_b < fin_a` | «interval overlap algorithm» |
| Códigos QR firmados | Cómo validar que un QR no fue alterado | «HMAC signed token QR ticket» |

## Bloque 6 · Mesa de ayuda (fase 6)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| C# moderno | Tipos por referencia anulables, `record`, `async/await`, LINQ | learn.microsoft.com: «C# guide» |
| ASP.NET Core Minimal APIs | Rutas, inyección de dependencias, configuración, filtros | learn.microsoft.com: «Minimal APIs overview» |
| Autenticación JWT | `JwtBearer` con `Authority` o `MetadataAddress` | learn.microsoft.com: «Configure JWT bearer authentication» |
| MongoDB | Documentos, embeber vs referenciar, índices, agregaciones | mongodb.com/docs: «Data Modeling», «Indexes» |
| Driver de C# | Colecciones tipadas, filtros, `CreateIndex` | mongodb.com/docs/drivers/csharp |
| Time series y TTL | Lecturas de dispositivos que se borran solas | mongodb.com/docs: «Time Series», «TTL Indexes» |
| Servicios en segundo plano | `BackgroundService`, temporizadores | learn.microsoft.com: «Background tasks with hosted services» |
| SLA | Tiempos de respuesta y solución por prioridad | «ITIL incident management SLA» |

## Bloque 7 · Tablero (fase 7)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Agregaciones SQL | `GROUP BY`, funciones de ventana básicas | «SQL GROUP BY tutorial» |
| Agregaciones MongoDB | Pipeline `$match`, `$group` | mongodb.com/docs: «Aggregation» |
| Composición en el portal | Juntar datos de varias APIs | microservices.io: «API Composition» |
| Gráficas | Barras, pastel, línea | recharts.org o chartjs.org |

## Bloque 8 · Calidad (fase 8)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Estrategia de pruebas | Pirámide, unitarias vs integración vs E2E | martinfowler.com: «The Practical Test Pyramid» |
| pytest | Fixtures, parametrización, `TestClient` de FastAPI | docs.pytest.org; FastAPI: «Testing» |
| JUnit 5 y Spring | `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest` | docs.spring.io: «Testing» |
| xUnit | Pruebas en .NET, `WebApplicationFactory` | learn.microsoft.com: «Integration tests in ASP.NET Core» |
| Testcontainers | Bases reales en Docker durante las pruebas | testcontainers.com |
| Pruebas de contrato | Validar la API contra su OpenAPI | schemathesis.readthedocs.io |
| Playwright | Recorridos E2E, selectores accesibles, trazas | playwright.dev: «Getting started», «Best practices» |

## Bloque 9 · Despliegue (fase 9)

| Tema | Qué debes entender | Dónde buscar |
|---|---|---|
| Docker | Imagen, capas, multi-stage, `.dockerignore` | docs.docker.com: «Get started», «Multi-stage builds» |
| GitHub Actions | Workflows, jobs, `paths`, secretos, `environment` | docs.github.com: «Understanding GitHub Actions» |
| OIDC | Desplegar sin guardar claves | docs.github.com: «About security hardening with OpenID Connect» |
| Azure Container Apps | Contenedores con escala a cero | learn.microsoft.com: «Azure Container Apps overview» |
| Cloud Run | Contenedores serverless | cloud.google.com/run/docs: «Quickstarts» |
| Vercel | Publicación desde Git | vercel.com/docs: «Git integration» |
| Observabilidad | Logs estructurados, correlación, salud | «structured logging JSON», «health check endpoint» |
