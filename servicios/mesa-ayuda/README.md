# Mesa de ayuda y monitoreo

**C# · ASP.NET Core 10 · MongoDB**

Gestiona tickets, SLA, dispositivos, telemetría y alertas. La API valida JWT RS256 mediante el
JWKS de Identidad, incluyendo firma, emisor, audiencia, vencimiento y tipo de token.

## Configuración y estado

Configura las variables locales con `.env.example` o secretos de usuario. En producción, el
servicio exige la configuración de MongoDB y de validación JWT; no inicia con el repositorio en
memoria ni con valores secretos de desarrollo. Las rutas y colecciones actuales aún incluyen
nombres en español, los IDs se crean como cadenas y JSON no tiene una política global
`snake_case`; por tanto, ADR-012, ADR-013 y ADR-014 siguen necesitando una migración compatible.

Las pruebas unitarias no demuestran compatibilidad con un MongoDB real.

## Comandos

Ejecuta desde esta carpeta:

```powershell
dotnet restore MesaAyuda.sln
dotnet test MesaAyuda.sln
dotnet run --project src/MesaAyuda.Api
```

La API local usa el puerto 8003 y publica su salud en `/salud`. Para construir la imagen:

```powershell
docker build -t exponexo-mesa-ayuda .
```

## CI/CD

`.github/workflows/mesa-ayuda.yml` compila y prueba con .NET 10. En `main`, publica en GHCR y
actualiza Azure Container Apps mediante OIDC, con su configuración como secretos de la Container
App. La bandeja de salida se publica cada 15 segundos en el tema SNS (`SNS_TEMA_EVENTOS_ARN`). Si
el JWKS de identidad no responde (por ejemplo, mientras despierta), se reintenta a los 10 segundos
conservando las llaves anteriores.
