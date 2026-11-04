# Pagos y facturación

**Java 25 · Spring Boot 4.1 · Flyway · Oracle**

Administra órdenes, cobros QR firmados, facturas, reembolsos y la bandeja de salida. La emisión
actual invoca el paquete PL/SQL `pkg_facturacion`; las pruebas usan H2 y no ejecutan ese paquete
contra Oracle.

## Configuración y estado

Usa `.env.example` para desarrollo. El perfil de producción valida la configuración crítica y no
debe usar las claves de ejemplo. La aplicación conserva nombres de rutas y columnas en español y
IDs de texto/UUID v4 en partes del modelo. ADR-012 y ADR-013 definen la migración coordinada que
aún no se ha aplicado. Jackson ya serializa JSON como `snake_case` según ADR-014.

## Comandos

Solo necesitas Java 25: el Maven Wrapper descarga la versión de Maven del proyecto. Ejecuta desde
esta carpeta:

```powershell
.\mvnw.cmd -B verify
.\mvnw.cmd spring-boot:run
.\mvnw.cmd -DskipTests package
```

La salud se consulta en `http://127.0.0.1:8002/actuator/health`. Para crear y probar la imagen:

```powershell
docker build -t exponexo-pagos .
docker run --env-file .env -p 8002:8002 exponexo-pagos
```

## CI/CD

`.github/workflows/pagos.yml` prueba con Java 25 y el wrapper. En `main`, publica en Google
Artifact Registry y despliega en Cloud Run mediante Workload Identity Federation, con su
configuración como variables de la revisión. El wallet de Oracle llega como zip en base64
(`ORACLE_WALLET_ZIP_BASE64`) y se descomprime al arrancar; JDBC lo lee con `oraclepki` sin
contraseña. La bandeja de salida publica los eventos en el tema SNS (`SNS_TEMA_EVENTOS_ARN`). Las
pruebas H2 no certifican compatibilidad con Oracle.
