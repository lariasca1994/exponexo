# Mesa de ayuda y monitoreo

**C# · ASP.NET Core 10**

Gestiona tickets, SLA, dispositivos, telemetría y alertas.

## Configuración

Usa `.env.example` o los secretos de usuario de .NET con tus propios valores (no se suben al
repositorio).

## Comandos

Desde esta carpeta:

```powershell
dotnet restore MesaAyuda.sln
dotnet test MesaAyuda.sln
dotnet run --project src/MesaAyuda.Api
```

La salud se consulta en `/salud`. Para construir la imagen:
`docker build -t exponexo-mesa-ayuda .`

Se publica sola desde GitHub en cada cambio a `main`, si pasan las pruebas. Las lecturas de los
dispositivos se depuran solas a los 15 días.
