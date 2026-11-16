# Pagos y facturación

**Java 25 · Spring Boot 4.1 · Flyway**

Administra órdenes, cobros con QR, facturas y reembolsos.

## Configuración

Usa `.env.example` para desarrollo con tus propios valores (no se sube al repositorio). Las pruebas
usan una base en memoria.

## Comandos

Solo necesitas Java 25: el Maven Wrapper descarga la versión de Maven del proyecto. Desde esta
carpeta:

```powershell
.\mvnw.cmd -B verify
.\mvnw.cmd spring-boot:run
```

La salud se consulta en `/actuator/health`. Para crear la imagen:
`docker build -t exponexo-pagos .`

Se publica sola desde GitHub en cada cambio a `main`, si pasan las pruebas.
