# Pagos y facturación

**Java · Spring Boot · Oracle Autonomous · Cloud Run**

Crea las órdenes de pago de stands y entradas, genera el cobro con QR, registra la aprobación,
emite la factura con su consecutivo (paquete PL/SQL `pkg_facturacion`) y gestiona reembolsos.

## Qué debes construir aquí

| Fase | Funcionalidad |
|---|---|
| 3 | Órdenes con idempotencia, cobro QR firmado, simulación de pago, factura con procedimiento almacenado |
| 4 | Bandeja de salida (`pago.aprobado`, `pago.rechazado`, `pago.reembolsado`) |
| 7 | Resumen de ingresos para el tablero |

## Archivos que vas a crear (estructura sugerida)

Spring Initializr genera la base (`pom.xml`, `mvnw`, la clase principal y `application.properties`).
Tú organizas el código por capas dentro del paquete `co.exponexo.pagos`:

```text
pagos/
├── src/main/java/co/exponexo/pagos/
│   ├── PagosApplication.java   Punto de entrada (lo genera Initializr).
│   ├── config/                 Seguridad (resource server con el JWKS de identidad), CORS,
│   │                           filtro del X-Correlation-Id y manejo global de errores
│   │                           (formato Problem Details).
│   ├── ordenes/                Entidad, repositorio, servicio y controlador de órdenes.
│   ├── qr/                     Generación y verificación del cobro QR firmado.
│   ├── facturas/               Llamada al paquete pkg_facturacion y consulta de facturas.
│   ├── reembolsos/             Registro de reembolsos.
│   ├── bandeja/                Bandeja de salida y su publicador periódico hacia la cola.
│   └── clientes/               Cliente HTTP hacia las rutas internas de identidad-reservas.
├── src/main/resources/
│   ├── application.properties  Configuración: lee las variables de entorno (nunca valores reales).
│   └── db/migration/           Flyway: V1__..., V2__... (tablas) y R__pkg_facturacion (PL/SQL).
├── src/test/java/...           JUnit 5: pruebas de servicio, controlador y repositorio.
├── Dockerfile                  Imagen para producción (fase 9).
├── .env.example                Plantilla de variables (ya está).
└── .env                        Tu copia con valores reales (no se sube).
```

## Qué estudiar antes

Bloque 3 de la [ruta de aprendizaje](../../docs/RUTA-DE-APRENDIZAJE.md). Tablas y procedimientos
en las secciones 2 y 4 del [modelo de datos](../../docs/MODELO-DE-DATOS.md); rutas en la
sección 2 de los [contratos de API](../../docs/CONTRATOS-API.md).

**Spring no lee archivos `.env` solo.** Investiga dos caminos y elige uno: variables de entorno del
sistema o de la configuración de ejecución de VS Code, o importar el archivo con
`spring.config.import` («spring.config.import optional file env properties»).

**El wallet de Oracle** se descarga desde la consola de la base (botón «Database connection»).
Descomprímelo en una carpeta **fuera del repositorio** o en `wallet/` (excluida por el
`.gitignore`) y apunta `ORACLE_WALLET_RUTA` a ella.

## Comandos de este servicio

| Para qué | Comando |
|---|---|
| Generar el proyecto (desde `servicios/`) | Ver la fase 3 del [manual](../../docs/MANUAL-DESARROLLO.md) |
| Copiar la plantilla de variables | `Copy-Item .env.example .env` |
| Levantar | `.\mvnw.cmd spring-boot:run` |
| Pruebas | `.\mvnw.cmd test` |
| Empaquetar | `.\mvnw.cmd -DskipTests package` |
| Salud | `http://127.0.0.1:8002/actuator/health` |
| Construir la imagen | `docker build -t exponexo-pagos .` |
| Probar la imagen | `docker run --env-file .env -p 8002:8002 exponexo-pagos` |

## Lista de chequeo del servicio

- [ ] Toda ruta (salvo salud) exige un JWT válido de identidad.
- [ ] El monto se obtiene del servicio de reservas, no del navegador.
- [ ] La misma `Idempotency-Key` no crea dos órdenes.
- [ ] Pagar dos veces la misma orden no genera dos facturas.
- [ ] Los montos usan `BigDecimal` y `NUMBER` con decimales fijos.
- [ ] El consecutivo de facturas no se repite ni salta con dos aprobaciones simultáneas.
