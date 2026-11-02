# ==============================================================================
# Dockerfile: mesa-ayuda (ASP.NET Core 9 / 10 Minimal APIs)
# Multi-stage build with .NET Runtime
# ==============================================================================
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS builder

WORKDIR /src

# Copy project files and restore
COPY src/MesaAyuda.Api/*.csproj src/MesaAyuda.Api/
RUN dotnet restore src/MesaAyuda.Api/MesaAyuda.Api.csproj

# Copy remaining source code and publish
COPY src/MesaAyuda.Api/ src/MesaAyuda.Api/
RUN dotnet publish src/MesaAyuda.Api/MesaAyuda.Api.csproj -c Release -o /app/publish /p:UseAppHost=false

# ==============================================================================
# Runner stage
# ==============================================================================
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runner

ENV ASPNETCORE_URLS=http://+:8003 \
    PORT=8003 \
    ASPNETCORE_ENVIRONMENT=Production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/publish .

# Run as non-root user (built into Microsoft .NET images as 'app')
USER $APP_UID

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8003/salud || exit 1

ENTRYPOINT ["dotnet", "MesaAyuda.Api.dll"]
