# ExpoNexo

**La plataforma que conecta un recinto de ferias con sus expositores y visitantes.**

ExpoNexo resuelve el día a día de un recinto de ferias y eventos: los expositores reservan y pagan
sus stands, los visitantes compran su entrada y agendan citas de negocios, y el personal del
recinto atiende incidentes y vigila los kioscos y pantallas durante el evento.

> Estado: **Completado (Fases 0 a 9 implementadas, probadas y verificadas)**. Cumple con la arquitectura distribuida definida en [docs/MANUAL-DESARROLLO.md](docs/MANUAL-DESARROLLO.md).

## Capacidades por Rol

| Para quién | Qué puede hacer |
|---|---|
| **Expositor** | Ver el plano interactivo de pabellones, reservar un stand con protección de concurrencia e idempotencia, pagar con QR HMAC, subir planos a Cloudinary, recibir su factura y gestionar agenda B2B con visitantes. |
| **Visitante** | Comprar su entrada, recibir credencial con código QR firmado anti-reutilización, ver expositores y agendar citas de negocios sin traslapes. |
| **Personal del recinto** | Escanear credenciales QR en accesos, abrir y atender tickets de soporte con SLA y monitorear kioscos/pantallas en tiempo real con apertura automática de incidencias ante desconexión. |
| **Administrador** | Crear y gestionar eventos, pabellones, stands y salas de reuniones, además de consultar el tablero consolidado con ocupación, recaudación financiera y métricas de soporte. |

## Arquitectura y Componentes

Cuatro servicios autónomos con bases de datos independientes, comunicación asíncrona mediante el patrón **Transactional Outbox**, y un portal web unificado en Progressive Web App (PWA):

| Carpeta | Servicio | Tecnología | Base de datos | Puerto Local |
|---|---|---|---|---|
| [portal/](portal/) | Portal PWA multiplataforma (Android, iOS, Desktop) | React 19 + TypeScript + Vite + PWA Workbox | — | 5173 / 8080 |
| [servicios/identidad-reservas/](servicios/identidad-reservas/) | Identidad (Argon2, TOTP, WebAuthn, RS256 JWKS), catálogo, reservas, entradas y agenda B2B | Python 3.12+ + FastAPI + SQLAlchemy + Alembic | SQL Server / SQLite (test) | 8001 |
| [servicios/pagos/](servicios/pagos/) | Órdenes de pago, cobros QR con firma HMAC, facturación y paquete PL/SQL | Java 21 + Spring Boot 3.4 + Flyway | Oracle Autonomous / H2 (test) | 8002 |
| [servicios/mesa-ayuda/](servicios/mesa-ayuda/) | Mesa de ayuda con cálculo de SLA, telemetría time-series y monitoreo de dispositivos | C# + ASP.NET Core Minimal APIs + Driver MongoDB | MongoDB Atlas (Time-Series & TTL) | 8003 |
| [servicios/eventos/](servicios/eventos/) | Consumidores SQS: `repartidor` (orquestación interna) y `avisos` (Brevo email y Telegram) | Python Serverless (AWS Lambda) | AWS SQS + DLQ | — |

## PWA y Experiencia de Usuario

- **Instalable en cualquier plataforma**: Android, iOS y Linux/Windows mediante manifest PWA, service worker con precaching y soporte offline.
- **Iconografía adaptable**: Set de íconos en alta resolución (SVG vectorial, 192x192, 512x512 maskable y Apple Touch Icon).
- **Diseño y Micro-interacciones**: Sistema de diseño basado en tokens CSS accesibles (`tokens.css`), retroalimentación visual, transiciones de estados y focus rings conformes a accesibilidad WCAG.
- **Gestión de Medios**: Carga y optimización de banners y planos de stands integrada con Cloudinary mediante firma segura en backend.

## Ejecución Rápida Local

### Opción 1: Docker Compose

```bash
docker compose up --build
```

Servicios disponibles en:
- Portal Web PWA: `http://localhost:8080`
- API Identidad y Reservas: `http://localhost:8001/docs` (Salud: `/salud`, JWKS: `/.well-known/jwks.json`)
- API Pagos: `http://localhost:8002/actuator/health`
- API Mesa de Ayuda: `http://localhost:8003/salud`

### Opción 2: Desarrollo Nativo

1. **Identidad y Reservas:**
   ```bash
   cd servicios/identidad-reservas
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:create_app --factory --port 8001 --reload
   ```

2. **Pagos:**
   ```bash
   cd servicios/pagos
   .\mvnw.cmd spring-boot:run
   ```

3. **Mesa de Ayuda:**
   ```bash
   cd servicios/mesa-ayuda
   dotnet run --project src/MesaAyuda.Api
   ```

4. **Portal:**
   ```bash
   cd portal
   npm install
   npm run dev
   ```

## Pruebas y Calidad

Cada servicio cuenta con su propia batería de pruebas automatizadas:

| Componente | Comando de Pruebas | Cobertura / Alcance |
|---|---|---|
| Identidad y Reservas | `pytest servicios/identidad-reservas/pruebas` | Autenticación, MFA, concurrencia de reservas, QR de tickets y agenda B2B |
| Pagos | `mvn test` (en `servicios/pagos`) | Idempotencia, firma HMAC de cobros QR, máquina de estados y outbox |
| Mesa de Ayuda | `dotnet test` (en `servicios/mesa-ayuda`) | SLA por prioridad y auto-ticket de dispositivos sin telemetría |
| Eventos | `pytest servicios/eventos/pruebas` | Despacho SQS, deduplicación e integración Brevo / Telegram |
| Integración E2E | `pytest pruebas/test_e2e_integration.py` | Ciclo de vida completo desde registro y reserva hasta validación de acceso en puerta |
| Portal Web | `npm run build` (en `portal`) | Chequeo estricto de tipos TypeScript y empaquetado PWA |

## Integración y Despliegue Continuo (CI/CD)

Configurado en [.github/workflows/](.github/workflows/):
- **OIDC Multi-Cloud**: Despliegue seguro sin llaves secretas estáticas (Azure Container Apps, Google Cloud Run, AWS Lambda).
- **Filtro de rutas (`paths`)**: Cada push a `main` compila y despliega exclusivamente el servicio modificado.
- **Auditoría Continua**: Escaneo programado semanal de dependencias vulnerables en Python, Java, .NET y Node.js.

## Documentación Técnica

- [Manual de desarrollo](docs/MANUAL-DESARROLLO.md)
- [Arquitectura distribuida](docs/ARQUITECTURA.md)
- [Modelo de datos](docs/MODELO-DE-DATOS.md)
- [Contratos de API](docs/CONTRATOS-API.md)
- [Catálogo de eventos](docs/EVENTOS.md)
- [Ruta de aprendizaje](docs/RUTA-DE-APRENDIZAJE.md)
- [Registro de decisiones arquitectónicas (ADRs)](docs/DECISIONES.md)
