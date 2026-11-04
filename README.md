# ExpoNexo

**La plataforma que conecta un recinto de ferias con sus expositores y visitantes.**

**En producción:** https://exponexo-portal.vercel.app

ExpoNexo resuelve el día a día de un recinto de ferias y eventos: los expositores reservan y pagan
sus stands, los visitantes compran su entrada y agendan citas de negocios, y el personal del
recinto atiende incidentes y vigila los kioscos y torniquetes durante el evento.

<p align="center">
  <img src="docs/capturas/portada.png" alt="Portada de ExpoNexo con los próximos eventos" width="100%">
</p>

## Qué puede hacer cada persona

| Para quién | Qué puede hacer |
|---|---|
| **Visitante** | Comprar su entrada con código QR de acceso, ver expositores y agendar citas de negocios sin cruces de horario. |
| **Expositor** | Elegir su stand en el plano del pabellón, pagarlo con QR, recibir la factura y atender su agenda de reuniones. |
| **Personal del recinto** | Validar entradas en la puerta, atender tickets de soporte con tiempos de atención y vigilar los dispositivos. |
| **Administrador** | Gestionar eventos, pabellones, stands y salas, y consultar el tablero de ocupación, recaudo y soporte. |

El registro público crea cuentas de visitante o expositor; el ingreso siempre pide verificación en
dos pasos (app autenticadora, código por correo o llave de acceso).

## Arquitectura

Cuatro servicios con su propia base de datos que se avisan por eventos (bandeja de salida → tema
SNS → una cola por función), y un portal web instalable:

| Carpeta | Servicio | Tecnología | Base de datos | Nube |
|---|---|---|---|---|
| [portal/](portal/) | Portal para todos los roles (PWA) | React 19 · TypeScript · Vite | — | Vercel |
| [servicios/identidad-reservas/](servicios/identidad-reservas/) | Cuentas, MFA, JWT, catálogo, reservas, entradas y agenda | Python · FastAPI | SQL Server | Azure Container Apps |
| [servicios/pagos/](servicios/pagos/) | Órdenes, cobro con QR firmado, facturación | Java 25 · Spring Boot 4 | Oracle Autonomous | Cloud Run |
| [servicios/mesa-ayuda/](servicios/mesa-ayuda/) | Tickets con SLA y monitoreo de dispositivos | C# · ASP.NET Core 10 | MongoDB Atlas | Azure Container Apps |
| [servicios/eventos/](servicios/eventos/) | Repartidor de eventos y avisos por correo y Telegram | Python | SNS + SQS | AWS Lambda |

Todo funciona con planes gratuitos y escala a cero: los servicios duermen sin tráfico y la base de
identidad se pausa sola, porque nada la consulta mientras nadie usa el sistema (la portada no toca
ningún servicio). La paleta del portal usa un color por base de datos: rojo SQL Server, rojo Oracle
y verde MongoDB.

## Ejecución local

```bash
docker compose up --build   # identidad :8001, pagos :8002, mesa de ayuda :8003
cd portal && npm ci && npm run dev   # portal en http://localhost:5173
```

Cada servicio también corre por separado; los comandos están en su README. Las variables van en el
`.env` de cada carpeta, a partir de su `.env.example`.

## Pruebas y calidad

| Componente | Comando | Qué cubre |
|---|---|---|
| Identidad | `python -m pytest pruebas` | Registro, MFA, reservas concurrentes, QR de entradas, agenda, configuración de producción |
| Pagos | `./mvnw verify` | Idempotencia, firma del QR, facturación, configuración de producción, wallet |
| Mesa de ayuda | `dotnet test` | SLA, JWT verificado, formato de MongoDB, configuración de producción |
| Eventos | `python -m pytest pruebas` | Reparto de eventos, idempotencia y avisos |
| Integración | `python -m pytest pruebas/test_e2e_integration.py` | Ciclo completo: registro, reserva, pago y acceso |
| Portal | `npm test && npm run build` | Sesión, tipos y empaquetado |

Además, [qa-evidencia](https://github.com/lariasca1994) prueba el sistema desplegado cada día hábil
(catálogo e ingreso fallido, con capturas) y el tablero de estado del portafolio vigila su salud.

## Despliegue

Todo sale de GitHub: cada push a `main` prueba y despliega el servicio que cambió. La configuración
de producción vive en el entorno `produccion` de GitHub y los workflows la entregan a cada nube
(ver [.github/workflows/](.github/workflows/README.md) e [infra/](infra/README.md)). Los datos de
demostración se cargan con el workflow *Poblar datos de demostración* ([datos-demo/](datos-demo/README.md)).

## Documentación

- [Manual de usuario](docs/MANUAL-USUARIO.md)
- [Manual de desarrollo](docs/MANUAL-DESARROLLO.md)
- [Arquitectura](docs/ARQUITECTURA.md) · [Modelo de datos](docs/MODELO-DE-DATOS.md) · [Contratos de API](docs/CONTRATOS-API.md) · [Eventos](docs/EVENTOS.md)
- [Decisiones de arquitectura (ADR)](docs/DECISIONES.md) · [Ruta de aprendizaje](docs/RUTA-DE-APRENDIZAJE.md)
