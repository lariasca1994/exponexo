# Manual de desarrollo de ExpoNexo

Este manual es tu guía para construir ExpoNexo **tú mismo**. No trae código: te dice qué construir,
en qué orden, qué estudiar antes, qué buscar, qué comandos ejecutar y cómo saber que terminaste
cada parte. El código lo escribes tú; cuando tengas dudas o quieras una revisión, pide ayuda
mostrando lo que hiciste (ver [la sección 9](#9-cómo-pedir-ayuda)).

## Contenido

1. [Cómo usar este manual](#1-cómo-usar-este-manual)
2. [Qué vas a construir](#2-qué-vas-a-construir)
3. [Prepara tu equipo](#3-prepara-tu-equipo)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Convenciones del proyecto](#5-convenciones-del-proyecto)
6. [Variables de entorno y secretos](#6-variables-de-entorno-y-secretos)
7. [Fases de desarrollo](#7-fases-de-desarrollo)
8. [Lista de chequeo antes de cada push](#8-lista-de-chequeo-antes-de-cada-push)
9. [Cómo pedir ayuda](#9-cómo-pedir-ayuda)

---

## 1. Cómo usar este manual

**Orden de lectura recomendado:**

1. Este manual completo, una vez, sin programar.
2. [ARQUITECTURA.md](ARQUITECTURA.md): entiende cómo se hablan los servicios.
3. [RUTA-DE-APRENDIZAJE.md](RUTA-DE-APRENDIZAJE.md): estudia lo de la fase que vas a empezar.
4. El README de la carpeta del servicio en que vas a trabajar: ahí está la lista de archivos que debes crear y qué hace cada uno.
5. [MODELO-DE-DATOS.md](MODELO-DE-DATOS.md) y [CONTRATOS-API.md](CONTRATOS-API.md) del servicio.

**Regla de oro:** termina una fase completa (funciona en local, tiene pruebas, está desplegada y
documentada) antes de empezar la siguiente. Una fase a medias en cada servicio es la forma más
segura de no terminar nunca.

**Cómo leer cada fase:** todas tienen la misma estructura:

| Apartado | Qué contiene |
|---|---|
| Objetivo | Qué debe poder hacer alguien al terminar la fase. |
| Estudia antes | Temas que necesitas entender antes de escribir la primera línea. |
| Busca | Palabras clave exactas para buscar en la documentación oficial. |
| Pasos | Qué construir, en orden, sin código. |
| Comandos | Lo que ejecutas en la terminal. |
| Terminado cuando | Criterios para saber que la fase está lista. |
| Errores comunes | Lo que suele salir mal y cómo reconocerlo. |

---

## 2. Qué vas a construir

ExpoNexo es la plataforma de un recinto de ferias. Tiene **cuatro servicios y un portal**:

| Parte | Responsabilidad única | Por qué esa tecnología |
|---|---|---|
| **Portal** (React + TypeScript) | Todas las pantallas para expositores, visitantes, personal y administradores. | Es el estándar del mercado para interfaces web. |
| **Identidad y reservas** (FastAPI + SQL Server) | Cuentas, verificación en dos pasos, emisión de tokens, catálogo de eventos y stands, reservas, entradas y citas. | Reglas transaccionales con cupos y fechas: terreno natural de una base relacional. |
| **Pagos** (Spring Boot + Oracle) | Órdenes de pago, cobro con QR, aprobación, facturas y reembolsos. | Java con Oracle es lo habitual en banca y facturación. |
| **Mesa de ayuda** (ASP.NET Core + MongoDB) | Tickets de soporte con SLA y monitoreo de kioscos y pantallas del recinto. | .NET es común en TI corporativa; las lecturas de dispositivos son documentos de mucho volumen. |
| **Eventos** (cola de mensajes + funciones serverless en Python) | Llevar mensajes entre servicios y enviar avisos por correo y Telegram. | Desacopla los servicios: ninguno espera al otro. |

**Flujo principal** (el que debe funcionar de punta a punta al final):

1. Un expositor se registra, activa su verificación en dos pasos e ingresa.
2. Ve el plano del evento y reserva un stand. La reserva queda «pendiente de pago» con vencimiento.
3. El servicio de pagos crea la orden y genera el QR.
4. Al aprobarse el pago, pagos publica el mensaje «pago aprobado».
5. Identidad y reservas lo recibe y marca la reserva como «pagada».
6. El servicio de eventos envía la factura y la confirmación por correo.
7. Si algo falla en el stand durante la feria, el expositor abre un ticket y la mesa de ayuda lo
   atiende con su SLA.

---

## 3. Prepara tu equipo

### 3.1 Herramientas que debes instalar

Ejecuta cada comando en PowerShell (Windows). Después de instalar, **cierra y abre la terminal**
para que se actualice el PATH.

| Herramienta | Para qué | Comando de instalación | Cómo verificar |
|---|---|---|---|
| Git | Control de versiones | `winget install Git.Git` | `git --version` |
| GitHub CLI | Repositorio, secretos y workflows desde la terminal | `winget install GitHub.cli` | `gh --version` |
| Python 3.14 | Identidad-reservas y eventos | `winget install Python.Python.3.14` | `python --version` |
| Node.js LTS | Portal y pruebas E2E | `winget install OpenJS.NodeJS.LTS` | `node --version` y `npm --version` |
| Java 25 LTS (Eclipse Temurin) | Servicio de pagos | `winget install EclipseAdoptium.Temurin.25.JDK` | `java -version` |
| .NET SDK 10 | Mesa de ayuda | `winget install Microsoft.DotNet.SDK.10` | `dotnet --version` |
| Docker Desktop | Construir y probar las imágenes de cada servicio | `winget install Docker.DockerDesktop` | `docker --version` |
| ODBC Driver 18 para SQL Server | Que Python se conecte a SQL Server | `winget install Microsoft.msodbcsql.18` | Aparece en «Orígenes de datos ODBC» de Windows |
| Azure CLI | Recursos de Azure | `winget install Microsoft.AzureCLI` | `az --version` |
| Google Cloud CLI | Cloud Run | `winget install Google.CloudSDK` | `gcloud --version` |
| AWS CLI | Cola de mensajes y funciones | `winget install Amazon.AWSCLI` | `aws --version` |
| Visual Studio Code | Editor | `winget install Microsoft.VisualStudioCode` | — |

**Regla obligatoria: todo en su última versión.** Las versiones viejas acumulan fallas de
seguridad conocidas. Esto vale para las herramientas de esta tabla, las librerías de cada servicio
y las imágenes base de Docker.

- Herramientas: `winget upgrade` lista lo que tiene versión nueva, y `winget upgrade --id <Id>`
  actualiza una. Revísalo al empezar cada fase y cuando llegue un aviso de seguridad.
- En los lenguajes con versión mayor y LTS (Node.js, Java, .NET), usa **la LTS más reciente**.
  En Python, usa la última versión estable.
- Librerías: busca «pip list --outdated», «npm outdated», «Maven versions plugin display-dependency-updates»
  y «dotnet list package --outdated».
- En la fase 9 automatiza la revisión: busca «Dependabot version updates» y «dependency-review-action».

**Extensiones de VS Code recomendadas** (búscalas por nombre en el panel de extensiones): Python,
Pylance, ESLint, Prettier, Extension Pack for Java, Spring Boot Extension Pack, C# Dev Kit,
MongoDB for VS Code, SQL Server (mssql), Docker, Playwright Test for VSCode.

### 3.2 Cuentas en la nube

Todo se despliega en planes gratuitos. Antes de la fase 1 necesitas tener creadas las cuentas y
los recursos que describe [infra/README.md](../infra/README.md). No los crees todos de una vez:
cada fase dice cuál necesitas.

### 3.3 Inicia sesión en las CLI

Cuando llegue la fase que lo necesite:

| Nube | Comando |
|---|---|
| GitHub | `gh auth login` |
| Azure | `az login` |
| Google Cloud | `gcloud auth login` y luego `gcloud config set project TU_PROYECTO` |
| AWS | `aws configure` (solo para tu equipo local; en GitHub se usa OIDC, sin claves) |

---

## 4. Estructura del repositorio

```text
exponexo/
├── README.md                  Presentación del producto
├── .gitignore                 Lo que nunca se sube (.env, builds, credenciales)
├── docs/                      Toda la documentación (este manual y sus anexos)
├── portal/                    React + TypeScript (lo creas en la fase 1)
├── servicios/
│   ├── identidad-reservas/    FastAPI + SQL Server
│   ├── pagos/                 Spring Boot + Oracle
│   ├── mesa-ayuda/            ASP.NET Core + MongoDB
│   └── eventos/               Funciones serverless en Python
├── pruebas/                   Pruebas E2E y de contrato
├── infra/                     Guía para crear los recursos en la nube
└── .github/workflows/         Despliegue continuo (los creas en la fase 9)
```

Cada carpeta tiene un **README** con: qué hace esa parte, qué archivos vas a crear y qué hace cada
uno, qué estudiar y los comandos propios. Esos README son tu mapa dentro de cada servicio.

---

## 5. Convenciones del proyecto

### 5.1 Idioma y nombres

- **Código en inglés o en español, pero uno solo en todo el proyecto.** En tu portafolio usas
  español; mantenerlo da coherencia. Decide en la fase 0 y anótalo en
  [DECISIONES.md](DECISIONES.md).
- **Tablas y columnas en `minusculas_con_guion_bajo`** (por ejemplo, `reservas_stand`).
- **Rutas de API en plural y en minúsculas** (por ejemplo, `/eventos/{id}/stands`).
- **Eventos entre servicios con el formato `entidad.accion` en pasado** (por ejemplo,
  `pago.aprobado`). Ver [EVENTOS.md](EVENTOS.md).

### 5.2 Ramas y commits

- Trabaja en ramas cortas: `fase-1-identidad`, `fase-2-reservas`… y únelas a `main` con un pull
  request, aunque trabajes solo (te acostumbra al flujo real y deja historial de revisión).
- Mensajes con el formato que ya usas: `tipo(alcance): descripción` en español. Ejemplos de
  tipos: `feat`, `fix`, `docs`, `test`, `ci`, `refactor`.
- Un commit = un cambio con sentido. Evita commits de «avances» con cosas mezcladas.

### 5.3 Documentación

- Cada vez que termines algo, actualiza el README del servicio y este manual si cambió un paso.
- **Nunca** escribas en la documentación: contraseñas, claves, correos reales, regiones,
  costos, ni detalles internos de seguridad (topes, excepciones, cómo se guardan los secretos).
  La seguridad se documenta solo como frase general.

---

## 6. Variables de entorno y secretos

- Cada servicio tiene un **`.env.example`** con todas las variables que necesita, explicadas y
  con valores de relleno. **Cópialo a `.env`** en la misma carpeta y completa los valores reales:
  `Copy-Item .env.example .env`
- **Cómo se nombran:** `<GRUPO>_<DETALLE>_<UNIDAD o TIPO>`, en mayúsculas y sin tildes, con la
  unidad o el tipo siempre al final (`JWT_ACCESO_MINUTOS`, `SQS_COLA_EVENTOS_URL`,
  `ORACLE_WALLET_RUTA`). Una misma cosa tiene el mismo nombre en todos los servicios. Solo se
  apartan de la regla los nombres que exige una librería o un SDK (`SPRING_PROFILES_ACTIVE`,
  `SERVER_PORT`, `ASPNETCORE_ENVIRONMENT`, `ASPNETCORE_URLS`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY` y el prefijo `VITE_`).
- **Etiquetas de cada variable** en los `.env.example`: `[SECRETO]` (nunca en el repositorio; en
  producción, como secreto), `[COMPARTIDA]` (mismo valor en los servicios indicados),
  `[DECIDES TÚ]` (elige el valor y anota el porqué en [DECISIONES.md](DECISIONES.md)) y `[FIJO]`
  (el nombre no se cambia).
- **Variables compartidas.** Si una cambia, cámbiala en todos los servicios donde aparece:

  | Variable | Identidad-reservas | Pagos | Mesa de ayuda | Eventos |
  |---|:-:|:-:|:-:|:-:|
  | `JWT_EMISOR`, `JWT_AUDIENCIA` | ✔ | ✔ | ✔ | |
  | `JWT_JWKS_URL` | | ✔ | ✔ | |
  | `CORS_ORIGENES_PERMITIDOS` | ✔ | ✔ | ✔ | |
  | `PORTAL_URL` | ✔ | ✔ | | ✔ |
  | `IDENTIDAD_URL` | | ✔ | | ✔ |
  | `INTERNO_SECRETO` | ✔ | ✔ | ✔ | ✔ |
  | `AWS_REGION`, `SQS_COLA_EVENTOS_URL` | ✔ | ✔ | ✔ | ✔ |
  | `BREVO_API_KEY`, `BREVO_REMITENTE_CORREO`, `BREVO_REMITENTE_NOMBRE` | ✔ | | | ✔ |

  En el portal, las direcciones de los servicios son `VITE_IDENTIDAD_URL`, `VITE_PAGOS_URL` y
  `VITE_MESA_AYUDA_URL`. Deben apuntar a los mismos servicios.
- El `.env` real **nunca** se sube: el `.gitignore` ya lo excluye. Compruébalo con
  `git status` antes de cada commit.
- En producción las variables no vienen de un archivo: se cargan como **secretos** en GitHub
  (`gh secret set NOMBRE --body "valor"`) y el workflow las pasa a la nube. Nunca uses una
  tubería de PowerShell para guardar un secreto (agrega un carácter invisible al inicio).
- Las claves que generas tú (firmas de tokens, cifrado) se crean con un generador aleatorio.
  Busca: «generate random 32 bytes base64 PowerShell» o usa `python -c` con el módulo
  `secrets` (investiga `secrets.token_urlsafe`).

---

## 7. Fases de desarrollo

### Fase 0 · Fundamentos (antes de programar)

**Objetivo:** tener el equipo listo, entender la arquitectura y tomar las decisiones base.

**Estudia antes:** qué es una arquitectura de microservicios y cuándo no conviene; qué es un
token JWT; qué es una variable de entorno; qué es una migración de base de datos.

**Busca:** «microservices database per service pattern», «JWT structure header payload
signature», «twelve-factor app config».

**Pasos:**

1. Instala todo lo de la [sección 3.1](#31-herramientas-que-debes-instalar) y verifica cada
   herramienta.
2. Lee [ARQUITECTURA.md](ARQUITECTURA.md) y dibuja en papel el flujo principal de la sección 2.
   Si no puedes dibujarlo sin mirar, vuelve a leer.
3. Decide el idioma del código y regístralo en [DECISIONES.md](DECISIONES.md).
4. Copia los `.env.example` a `.env` en cada carpeta (todavía con valores de relleno).
5. Elige la plantilla visual (ver [DISENO.md](DISENO.md)). Puedes cambiarla después.
6. Crea tu repositorio privado en GitHub y sube el esqueleto (los comandos están en la
   [fase 9](#fase-9--despliegue-continuo), primer párrafo).

**Terminado cuando:** todas las herramientas responden a su comando de verificación, tienes el
dibujo del flujo y las decisiones anotadas.

---

### Fase 1 · Identidad y portal con ingreso

**Objetivo:** una persona puede registrarse, configurar su verificación en dos pasos (app
autenticadora o código por correo), ingresar y ver una pantalla de inicio protegida en el portal.

**Estudia antes:**

- FastAPI: rutas, modelos de Pydantic, dependencias (`Depends`), manejo de errores.
- SQLAlchemy 2 (estilo moderno con `Mapped` y `mapped_column`) y Alembic para migraciones.
- Conexión a SQL Server desde Python con `pyodbc` y la cadena de conexión de SQLAlchemy.
- Hash de contraseñas con Argon2 (por qué no se usa SHA-256 para contraseñas).
- TOTP (RFC 6238): cómo funcionan las apps autenticadoras.
- JWT firmados con **RS256** (clave privada para firmar, pública para verificar) y el formato
  **JWKS**, que permite a los otros servicios verificar los tokens sin conocer la clave privada.
- React: componentes, estado, React Router y llamadas a una API con `fetch` o TanStack Query.

**Busca:**

- «FastAPI bigger applications APIRouter»
- «SQLAlchemy 2.0 ORM quickstart mapped_column»
- «Alembic autogenerate tutorial»
- «SQLAlchemy mssql pyodbc connection string ODBC Driver 18»
- «argon2-cffi PasswordHasher»
- «pyotp TOTP provisioning_uri»
- «PyJWT RS256 sign verify» y «JWKS endpoint example»
- «Vite React TypeScript template», «React Router tutorial», «TanStack Query getting started»

**Pasos:**

1. **Base de datos:** crea la base en Azure SQL (ver [infra/README.md](../infra/README.md)) y
   llena el `.env` de identidad-reservas.
2. **Proyecto de FastAPI:** crea el entorno virtual e instala dependencias (comandos abajo).
   Crea la estructura de carpetas que describe
   [servicios/identidad-reservas/README.md](../servicios/identidad-reservas/README.md).
3. **Configuración:** una clase que lea el `.env` (investiga `pydantic-settings`). Ninguna
   variable se lee directamente en el resto del código.
4. **Modelos y migración inicial:** tablas `usuarios`, `factores_mfa`, `codigos_respaldo`,
   `sesiones` e `intentos_ingreso` del [modelo de datos](MODELO-DE-DATOS.md). Genera la
   migración con Alembic y aplícala.
5. **Registro:** valida correo único y contraseña fuerte; guarda solo el hash.
6. **Ingreso en dos pasos:** la contraseña correcta **no** abre sesión; entrega un «pase» corto
   (pocos minutos) que solo sirve para el segundo paso. El segundo paso verifica el código de la
   app o del correo y recién ahí entrega los tokens.
7. **Tokens:** un token de acceso corto (minutos) y uno de refresco largo (días), guardado como
   huella en `sesiones` para poder revocarlo. Publica la clave pública en `/.well-known/jwks.json`.
8. **Portal:** crea el proyecto de React (comandos abajo), las pantallas de registro, ingreso,
   segundo paso, configuración de la app autenticadora (con el QR) e inicio. Guarda el token en
   memoria (investiga por qué no conviene `localStorage` para tokens).
   Conviértelo en **PWA** (instalable y con pantalla sin conexión): estudia «web app manifest»,
   «service worker lifecycle», «vite-plugin-pwa» y «workbox caching strategies»; instala con
   `npm install -D vite-plugin-pwa`. Nunca guardes en caché respuestas de la API con datos
   personales; solo los archivos de la interfaz.
9. **Pruebas:** registro, ingreso correcto, contraseña incorrecta, código incorrecto, código
   reutilizado y bloqueo tras varios intentos.

**Comandos:**

| Para qué | Comando (desde la carpeta del servicio) |
|---|---|
| Crear el entorno virtual | `python -m venv .venv` |
| Activarlo | `.venv\Scripts\Activate.ps1` |
| Instalar lo de esta fase | `pip install fastapi "uvicorn[standard]" "sqlalchemy>=2" alembic pyodbc pydantic-settings argon2-cffi pyotp "pyjwt[crypto]" "qrcode[pil]" httpx pytest` |
| Congelar dependencias | `pip freeze > requirements.txt` (revisa el archivo y deja solo lo que usas) |
| Iniciar Alembic | `alembic init migraciones` |
| Crear una migración | `alembic revision --autogenerate -m "usuarios y mfa"` |
| Aplicarla | `alembic upgrade head` |
| Levantar el servicio | `uvicorn app.main:app --reload --port 8001` |
| Ver la documentación automática | Abre `http://127.0.0.1:8001/docs` |
| Correr pruebas | `pytest -q` |
| Crear el portal (desde `exponexo/`) | `npm create vite@latest portal -- --template react-ts` y, cuando avise que la carpeta no está vacía, elige «Ignore files and continue» (no «Remove existing files») |
| Instalar dependencias del portal | `cd portal` y luego `npm install` y `npm install react-router-dom @tanstack/react-query` |
| Levantar el portal | `npm run dev` |

**Terminado cuando:** te registras, activas la app autenticadora con el QR, cierras sesión,
vuelves a entrar con contraseña y código, y el portal muestra tu nombre; las pruebas pasan; el
README del servicio refleja lo hecho.

**Ampliación de la fase 1 · Llaves de acceso (WebAuthn):** cuando el ingreso con contraseña y
código funcione, agrega el ingreso con llave de acceso (Windows Hello, huella o PIN del
dispositivo) como alternativa sin contraseña. Estudia: qué es WebAuthn y FIDO2, el «relying party»
(`rp_id` y origen), el registro (attestation) y el ingreso (assertion), el contador de firmas.
Busca: «WebAuthn guide», «py_webauthn registration authentication», «navigator.credentials.create
get», «passkeys relying party id localhost». Tabla nueva: `llaves_acceso` del
[modelo de datos](MODELO-DE-DATOS.md). Instala con `pip install webauthn`. Terminado cuando
registras tu dispositivo en el perfil y entras solo con la llave.

**Errores comunes:**

- *«Data source name not found»*: falta el ODBC Driver 18 o el nombre del driver en la cadena de
  conexión no coincide.
- *Tokens que «no validan» en otro servicio*: el `iss` o el `aud` no coinciden con lo que espera
  quien verifica.
- *Códigos TOTP que siempre fallan*: la hora del equipo está desfasada; activa la hora automática.

---

### Fase 2 · Catálogo de eventos y reservas de stands

**Objetivo:** el administrador crea eventos, pabellones y stands; un expositor ve el plano,
reserva un stand y la reserva queda «pendiente de pago» con fecha de vencimiento.

**Estudia antes:** transacciones y niveles de aislamiento; restricciones `UNIQUE` y llaves
foráneas; cómo evitar que dos personas reserven el mismo stand al mismo tiempo (concurrencia);
control de acceso por rol (RBAC).

**Busca:** «SQL Server unique filtered index», «optimistic concurrency rowversion SQL Server»,
«SQLAlchemy session transaction begin», «FastAPI role based access dependency», «idempotency key
API design».

**Pasos:**

1. Tablas `empresas`, `eventos`, `pabellones`, `stands` y `reservas_stand` del
   [modelo de datos](MODELO-DE-DATOS.md), con su migración.
2. Rutas de administración (solo rol administrador) para crear y editar eventos, pabellones y
   stands.
3. Ruta pública para listar eventos y el estado de sus stands (disponible, reservado, pagado).
4. Reserva con **procedimiento almacenado** (PA): escribe en SQL Server el procedimiento
   `reservar_stand`, que en una sola transacción comprueba que el stand esté libre, crea la
   reserva `pendiente_pago` con vencimiento (por ejemplo, 30 minutos) y escribe `reserva.creada`
   en `bandeja_salida` (ver [EVENTOS.md](EVENTOS.md)). FastAPI solo lo llama y traduce su
   resultado. Estudia: «T-SQL CREATE PROCEDURE», «TRY CATCH THROW T-SQL», «SET XACT_ABORT ON»,
   «UPDLOCK HOLDLOCK hints», «call stored procedure SQLAlchemy text» y cómo versionar el
   procedimiento dentro de una migración de Alembic (`op.execute`).
5. Vencimiento: un proceso que pase a `vencida` las reservas no pagadas a tiempo y libere el
   stand (investiga tareas programadas; en producción será una ejecución periódica).
6. Portal: plano o cuadrícula de stands con colores por estado, detalle del stand y botón
   «Reservar».
7. Pruebas: dos reservas simultáneas del mismo stand (solo una debe ganar), reserva vencida,
   acceso sin rol.

**Comandos:** los de la fase 1 (nuevas migraciones con `alembic revision --autogenerate`).

**Terminado cuando:** dos ventanas del navegador intentando reservar el mismo stand no pueden
lograrlo ambas; una reserva no pagada vence y el stand vuelve a estar disponible.

**Errores comunes:** olvidar la transacción (aparecen reservas dobles); comparar fechas sin zona
horaria (usa siempre UTC en la base y convierte solo al mostrar).

---

### Fase 3 · Pagos y facturación

**Objetivo:** al reservar un stand o comprar una entrada se crea una orden de pago con QR; al
aprobarse, se emite la factura y se avisa a los demás servicios.

**Estudia antes:**

- Spring Boot: controladores REST, servicios, repositorios con Spring Data JPA, validación.
- Flyway para migraciones en Java.
- Conexión a Oracle Autonomous con **Wallet** desde Java (JDBC con TNS).
- Spring Security como **Resource Server**: validar los JWT de identidad usando su JWKS.
- Máquina de estados de una orden de pago.
- Idempotencia: por qué el mismo pago no debe procesarse dos veces.
- Números consecutivos de facturas en Oracle con secuencias.

**Busca:**

- «Spring Initializr dependencies web data-jpa validation flyway oracle»
- «Spring Boot Oracle Autonomous Database wallet JDBC»
- «Spring Security OAuth2 resource server jwk-set-uri»
- «Flyway Oracle migration naming V1__»
- «Oracle sequence invoice number»
- «payment state machine pending approved rejected»
- «EMVCo QR code merchant presented» (para entender la estructura de un QR de cobro)

**Pasos:**

1. Crea la base Oracle Autonomous y descarga su wallet (ver [infra/README.md](../infra/README.md)).
2. Genera el proyecto con Spring Initializr (comando abajo) dentro de `servicios/pagos/`.
3. Migraciones con Flyway para `ordenes_pago`, `transacciones`, `cobros_qr`, `facturas`,
   `detalle_factura`, `reembolsos`, `eventos_procesados` y `bandeja_salida`.
4. Seguridad: toda ruta exige un JWT válido de identidad (configura el JWKS en el `.env`).
5. Crear orden: recibe la referencia (reserva o entrada) y el monto que indica el servicio de
   reservas, nunca el monto que envía el navegador.
6. Generar el QR de cobro con vencimiento y una firma que impida modificarlo.
7. Simular la aprobación (en un recinto real la daría el banco): una ruta interna o una pantalla
   de «pagar» que cambie la orden a `aprobada`.
8. Al aprobar, con **procedimiento almacenado en PL/SQL**: el paquete `pkg_facturacion` con el
   procedimiento `emitir_factura`, que en una transacción toma el consecutivo de la secuencia,
   crea la factura y su detalle, marca la orden `aprobada` y escribe `pago.aprobado` en la bandeja
   de salida. Spring lo invoca. Estudia: «PL/SQL package specification body», «PL/SQL exception
   handling RAISE_APPLICATION_ERROR», «Oracle sequence NEXTVAL», «Spring SimpleJdbcCall» o
   «JPA @Procedure / StoredProcedureQuery» y cómo versionarlo con Flyway (migraciones repetibles
   `R__`).
9. Pruebas con JUnit 5: orden duplicada, pago repetido (idempotencia), QR vencido, token ausente.

**Comandos:**

| Para qué | Comando |
|---|---|
| Generar el proyecto (desde `servicios/`) | `curl.exe https://start.spring.io/starter.zip -d type=maven-project -d language=java -d javaVersion=21 -d groupId=co.exponexo -d artifactId=pagos -d name=pagos -d dependencies=web,data-jpa,validation,flyway,oracle,oauth2-resource-server,actuator -o pagos.zip` |
| Descomprimir | `Expand-Archive pagos.zip -DestinationPath pagos -Force` y borra el zip |
| Levantar el servicio | `.\mvnw.cmd spring-boot:run` (desde `servicios/pagos/`) |
| Correr pruebas | `.\mvnw.cmd test` |
| Empaquetar | `.\mvnw.cmd -DskipTests package` |
| Ver salud | `http://127.0.0.1:8002/actuator/health` |

**Terminado cuando:** reservas un stand, se genera el QR, lo «pagas», la orden queda aprobada con
factura y el mensaje `pago.aprobado` aparece en la bandeja de salida.

**Errores comunes:** el wallet no se encuentra (revisa la ruta y la variable `TNS_ADMIN`); el
token llega pero Spring responde 401 (revisa `issuer` y `audience`); usar `double` para dinero
(usa `BigDecimal` y `NUMBER` con decimales fijos en Oracle).

---

### Fase 4 · Eventos entre servicios y avisos

**Objetivo:** los mensajes de la bandeja de salida llegan a una cola; una función los reparte:
avisa a reservas que el pago se aprobó y envía correos y mensajes de Telegram.

**Estudia antes:** el patrón **Transactional Outbox** (por qué no se publica directo a la cola
dentro de la transacción); colas con **cola de errores** (DLQ); entrega «al menos una vez» e
idempotencia del consumidor; funciones serverless.

**Busca:** «transactional outbox pattern», «Amazon SQS dead-letter queue», «AWS Lambda SQS
trigger Python», «boto3 SQS send_message», «Brevo transactional email API», «Telegram Bot API
sendMessage», «idempotent consumer».

**Pasos:**

1. Crea la cola principal y su cola de errores (comandos abajo).
2. En cada servicio con bandeja de salida, un proceso periódico que lea los mensajes no
   publicados, los envíe a la cola y los marque como publicados.
3. Función `repartidor` (en `servicios/eventos/`): según el tipo de mensaje, llama a la ruta
   interna del servicio que corresponde (por ejemplo, `pago.aprobado` → reservas marca la
   reserva como pagada).
4. Función `avisos`: correos con Brevo (confirmación de reserva, factura) y Telegram (alertas
   para el personal).
5. Cada consumidor guarda el `id` del mensaje ya procesado para ignorar repeticiones.
6. Pruebas: el mismo mensaje dos veces no duplica efectos; un mensaje que falla tres veces termina
   en la cola de errores.

**Comandos:**

| Para qué | Comando |
|---|---|
| Crear la cola de errores | `aws sqs create-queue --queue-name exponexo-eventos-errores` |
| Crear la cola principal | `aws sqs create-queue --queue-name exponexo-eventos` (luego investiga cómo asociarle la cola de errores con `RedrivePolicy`) |
| Ver la URL de una cola | `aws sqs get-queue-url --queue-name exponexo-eventos` |
| Empaquetar una función | Crea la carpeta de dependencias con `pip install -r requirements.txt -t paquete` y comprime con `Compress-Archive` |
| Probar una función en la nube | `aws lambda invoke --function-name exponexo-avisos salida.json` |

**Terminado cuando:** pagas un stand y, sin que el navegador haga nada más, la reserva pasa a
«pagada» y llega el correo de confirmación.

---

### Fase 5 · Entradas y citas de negocios

**Objetivo:** los visitantes compran su entrada (con QR de acceso) y piden citas a los
expositores en franjas disponibles; el expositor acepta o rechaza.

**Estudia antes:** cómo detectar choques de horarios (intervalos que se solapan); zonas horarias;
generación de códigos QR únicos y verificables.

**Busca:** «SQL overlapping time ranges query», «interval overlap condition start < end»,
«QR code ticket validation signed token».

**Pasos:**

1. Tablas `entradas`, `disponibilidad`, `salas` y `citas` del [modelo de datos](MODELO-DE-DATOS.md).
2. Compra de entrada: crea la entrada `pendiente_pago`, pide la orden a pagos y la activa cuando
   llega `pago.aprobado`.
3. Disponibilidad del expositor por día del evento; propuesta de cita solo en franjas libres de
   ambos y sin choques.
4. Aceptar o rechazar; al aceptar, publicar `cita.aceptada` (aviso por correo a ambos).
5. Portal: «Mi entrada» con su QR, agenda del expositor y del visitante.

**Terminado cuando:** dos citas que se solapan para la misma persona no pueden aceptarse; la
entrada pagada muestra su QR.

---

### Fase 6 · Mesa de ayuda y monitoreo

**Objetivo:** expositores y personal abren tickets con prioridad y SLA; los kioscos y pantallas
reportan su estado y, si dejan de reportar, se abre un ticket solo.

**Estudia antes:**

- ASP.NET Core con **Minimal APIs**, inyección de dependencias y configuración.
- Driver oficial de MongoDB para .NET: colecciones, filtros, índices.
- Colecciones **time series** de MongoDB e índices **TTL** (borran solos lo viejo).
- Autenticación JWT en ASP.NET Core usando el JWKS de identidad.
- Cálculo de vencimiento de SLA por prioridad.

**Busca:** «ASP.NET Core minimal APIs tutorial», «MongoDB C# driver quick start», «MongoDB time
series collections», «MongoDB TTL index», «ASP.NET Core JwtBearer Authority MetadataAddress»,
«BackgroundService .NET».

**Pasos:**

1. Crea el clúster gratuito de MongoDB Atlas (ver [infra/README.md](../infra/README.md)).
2. Crea el proyecto y el de pruebas (comandos abajo).
3. Colecciones `tickets`, `politicas_sla`, `dispositivos`, `lecturas` y `alertas` del
   [modelo de datos](MODELO-DE-DATOS.md), con sus índices (incluido el TTL de 15 días en
   `lecturas`).
4. Tickets: crear, asignar, cambiar estado (con historial), escalar de nivel cuando el SLA está
   por vencer.
5. Dispositivos: registro con un código de enrolamiento y reporte periódico de lecturas.
6. Un servicio en segundo plano que detecte dispositivos sin reportar y abra el ticket y la alerta.
7. Publicar `ticket.creado` y `ticket.sla_vencido` (avisos por Telegram al personal).
8. Pruebas con xUnit.

**Comandos:**

| Para qué | Comando (desde `servicios/mesa-ayuda/`) |
|---|---|
| Crear la API | `dotnet new webapi -n MesaAyuda.Api -o src/MesaAyuda.Api` |
| Crear las pruebas | `dotnet new xunit -n MesaAyuda.Pruebas -o pruebas/MesaAyuda.Pruebas` |
| Crear la solución y unirlas | `dotnet new sln -n MesaAyuda`, `dotnet sln add src/MesaAyuda.Api pruebas/MesaAyuda.Pruebas` |
| Paquetes | `dotnet add src/MesaAyuda.Api package MongoDB.Driver` y `dotnet add src/MesaAyuda.Api package Microsoft.AspNetCore.Authentication.JwtBearer` |
| Levantar | `dotnet run --project src/MesaAyuda.Api` |
| Pruebas | `dotnet test` |

**Terminado cuando:** un kiosco que deja de reportar genera un ticket y un aviso en Telegram; un
ticket muestra cuánto falta para vencer su SLA.

---

### Fase 7 · Tablero del administrador

**Objetivo:** ocupación de stands, ingresos, entradas vendidas, citas y tickets por evento.

**Estudia antes:** agregaciones en SQL (`GROUP BY`), agregaciones en MongoDB (pipeline), patrón
**Backend for Frontend** o composición de datos en el portal; gráficas en React.

**Busca:** «SQL Server GROUP BY date», «MongoDB aggregation pipeline group», «Recharts» o «Chart.js
React», «API composition pattern».

**Pasos:** cada servicio expone un resumen de sus propios datos; el portal los combina en un
tablero (no consultes la base de otro servicio).

**Terminado cuando:** el tablero muestra datos de los tres servicios y se actualiza al recargar.

---

### Fase 8 · Calidad

**Objetivo:** confianza en cada cambio.

**Estudia antes:** pirámide de pruebas; pruebas de contrato (que lo que dice el OpenAPI sea lo que
la API hace); Playwright.

**Busca:** «testing pyramid», «schemathesis OpenAPI testing», «Playwright getting started»,
«Testcontainers» (bases reales en pruebas con Docker), «JUnit 5 Spring Boot test slices».

**Pasos:** pruebas unitarias y de integración en cada servicio; pruebas de contrato de cada
OpenAPI; recorridos E2E del flujo principal (en `pruebas/` y luego en qa-evidencia); agrega
ExpoNexo al monitoreo de portafolio-status.

**Comandos:** `npm init playwright@latest` (en `pruebas/`), `npx playwright test`,
`npx playwright show-report`.

**Terminado cuando:** el flujo principal completo pasa en E2E contra producción.

---

### Fase 9 · Despliegue continuo

**Objetivo:** cada push a `main` despliega solo el servicio que cambió, sin claves guardadas.

**Estudia antes:** GitHub Actions (eventos, `paths`, jobs, `environment`, secretos); OIDC entre
GitHub y cada nube; contenedores Docker y registros de imágenes.

**Busca:** «GitHub Actions paths filter», «GitHub OIDC Azure login», «GitHub OIDC Google Cloud
Workload Identity Federation», «GitHub OIDC AWS assume role», «Dockerfile multi-stage build»,
«Vercel Git integration».

**El repositorio en GitHub lo creas tú** (puede ser desde la fase 0): desde `A:\Github\exponexo`
ejecuta `git init -b main`, `git add .`, `git commit -m "docs: esqueleto y manual de desarrollo"`
y `gh repo create exponexo --private --source . --push`. Antes del primer commit, `git status`
no debe mostrar ningún `.env`.

**Pasos:** un workflow por servicio (ver [.github/workflows/README.md](../.github/workflows/README.md)),
cada uno: pruebas → construir imagen → desplegar → comprobar salud. El portal se publica con la
integración de Git de Vercel.

**Terminado cuando:** cambias un texto del portal, haces push y lo ves en producción sin tocar
ninguna consola.

---

## 8. Lista de chequeo antes de cada push

- [ ] `git status` no muestra ningún `.env`, wallet ni certificado.
- [ ] Las pruebas del servicio que cambiaste pasan.
- [ ] El README del servicio describe lo que hiciste.
- [ ] El mensaje del commit sigue el formato `tipo(alcance): descripción`.
- [ ] No dejaste contraseñas, correos reales ni detalles de seguridad en documentación ni código.

## 9. Cómo pedir ayuda

Cuando te atasques, comparte:

1. **Qué intentabas hacer** (la fase y el paso).
2. **Qué hiciste** (el archivo o el fragmento que escribiste).
3. **Qué pasó** (el error completo, copiado tal cual, o lo que esperabas y no ocurrió).

La ayuda en este proyecto es de guía: explicación del error, qué revisar, qué leer y por qué. El
código lo corriges tú.
