# Mesa de ayuda y monitoreo del recinto

**C# · ASP.NET Core · MongoDB Atlas · Azure Container Apps**

Tickets de soporte con prioridad, niveles (N1, N2, N3) y SLA; registro y monitoreo de kioscos,
pantallas y torniquetes del recinto, con apertura automática de tickets cuando un dispositivo deja
de reportar.

## Qué debes construir aquí

| Fase | Funcionalidad |
|---|---|
| 6 | Tickets con historial y SLA, políticas por prioridad, enrolamiento y lecturas de dispositivos, detección de dispositivos caídos |
| 4 y 6 | Bandeja de salida (`ticket.creado`, `ticket.sla_vencido`, `dispositivo.caido`) |
| 7 | Resumen de tickets y cumplimiento de SLA para el tablero |

## Archivos que vas a crear (estructura sugerida)

```text
mesa-ayuda/
├── MesaAyuda.sln                   Solución que une la API y las pruebas.
├── src/MesaAyuda.Api/
│   ├── Program.cs                  Configuración: autenticación JWT con el JWKS de identidad,
│   │                               CORS, MongoDB, rutas y servicios en segundo plano.
│   ├── Configuracion/              Clases que leen la configuración (patrón Options).
│   ├── Datos/                      Acceso a MongoDB: colecciones e índices (incluido el TTL de
│   │                               las lecturas y la colección time series).
│   ├── Tickets/                    Modelo, reglas del SLA y rutas de tickets.
│   ├── Dispositivos/               Enrolamiento, lecturas y estado.
│   ├── Alertas/                    Servicio en segundo plano que detecta dispositivos sin reporte.
│   ├── Bandeja/                    Bandeja de salida y su publicador hacia la cola.
│   └── appsettings.json            Valores no secretos; los secretos llegan por variables de entorno.
├── pruebas/MesaAyuda.Pruebas/      xUnit: reglas del SLA, rutas y acceso a datos.
├── Dockerfile                      Imagen para producción (fase 9).
├── .env.example                    Plantilla de variables (ya está).
└── .env                            Tu copia con valores reales (no se sube).
```

## Qué estudiar antes

Bloque 6 de la [ruta de aprendizaje](../../docs/RUTA-DE-APRENDIZAJE.md). Colecciones en la
sección 3 del [modelo de datos](../../docs/MODELO-DE-DATOS.md); rutas en la sección 3 de los
[contratos de API](../../docs/CONTRATOS-API.md).

**.NET no lee archivos `.env` solo.** Investiga: «dotnet user-secrets» (recomendado para tu equipo)
o el paquete «DotNetEnv». En producción, las variables llegan como secretos de la Container App.
Las variables usan los mismos nombres planos que los demás servicios (por ejemplo, `MONGO_URI` o
`JWT_EMISOR`), así se reconocen de un vistazo entre servicios. Para leerlas agrupadas en clases de
configuración, investiga «ASP.NET Core options pattern» y «IConfiguration GetValue environment
variables».

## Comandos de este servicio

| Para qué | Comando (desde esta carpeta) |
|---|---|
| Crear la API, las pruebas y la solución | Ver la fase 6 del [manual](../../docs/MANUAL-DESARROLLO.md) |
| Guardar un secreto local | `dotnet user-secrets init --project src/MesaAyuda.Api` y `dotnet user-secrets set "Mongo:Uri" "VALOR" --project src/MesaAyuda.Api` |
| Levantar | `dotnet run --project src/MesaAyuda.Api` |
| Pruebas | `dotnet test` |
| Revisar paquetes vulnerables | `dotnet list package --vulnerable --include-transitive` |
| Construir la imagen | `docker build -t exponexo-mesa .` |

## Lista de chequeo del servicio

- [ ] Los tickets guardan cada cambio de estado en su historial.
- [ ] El vencimiento del SLA se calcula según la política de su prioridad.
- [ ] Las lecturas viejas se borran solas (índice TTL).
- [ ] Un dispositivo que deja de reportar abre un ticket una sola vez (no uno por minuto).
- [ ] Los dispositivos se autentican con su propio mecanismo, no con el token de una persona.
