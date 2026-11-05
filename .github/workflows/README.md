# Flujos de GitHub Actions

Los archivos de esta carpeta automatizan pruebas, auditorías y, en `main`, publicación o
despliegue de los servicios. La existencia de un flujo no implica que sus secretos, permisos,
recursos de nube o condiciones externas ya estén configurados.

| Archivo | Ejecución | Trabajo principal |
|---|---|---|
| `identidad-reservas.yml` | `push`/solicitud de cambio que afecta el servicio; ejecución manual | Pruebas con Python 3.14 y SQLite; publica en GHCR y actualiza Azure Container Apps en `main`. |
| `pagos.yml` | `push`/solicitud de cambio que afecta el servicio; ejecución manual | Pruebas con Java 25 y el Maven Wrapper; publica en Google Artifact Registry y despliega en Cloud Run con su configuración en `main`. |
| `mesa-ayuda.yml` | `push`/solicitud de cambio que afecta el servicio; ejecución manual | Pruebas con .NET 10; publica en GHCR y actualiza Azure Container Apps en `main`. |
| `eventos.yml` | `push`/solicitud de cambio que afecta el servicio; ejecución manual | Pruebas Python 3.14; empaqueta y actualiza las dos funciones Lambda con sus variables y fija la retención de logs en 14 días en `main`. |
| `e2e.yml` | `push`, solicitud de cambio y ejecución manual | Ejecuta el recorrido E2E con SQLite y, en un segundo trabajo, contra un SQL Server real en contenedor (migraciones y procedimientos). |
| `seguridad.yml` | Cada lunes, solicitud de cambio y ejecución manual | Auditoría pip, npm, NuGet y Maven; termina con error si una herramienta configurada falla. |
| `depuracion.yml` | Días 1 y 16 de cada mes; ejecución manual | Limpieza quincenal para no acumular espacio que pueda generar costo: en GitHub conserva las 5 imágenes más recientes de cada servicio en GHCR y borra cachés, artefactos y ejecuciones con más de 15 días; en las tres bases borra lo vencido con más de 15 días (intentos de ingreso, auditoría, códigos, sesiones y bandejas publicadas en Azure SQL; bandeja, eventos procesados y cobros QR vencidos en Oracle; bandeja publicada en MongoDB, cuyas lecturas de dispositivos vencen solas a los 15 días). |
| `capturas-manual.yml` | `push` que cambia `portal/`; ejecución manual | Espera la publicación del portal en Vercel, regenera las capturas del [manual](../../docs/MANUAL.md) con Playwright y sube un commit solo si alguna cambió. |
| `poblar-datos.yml` | Ejecución manual | Genera los datos de demostración y, si se pide, los carga en producción. |
| `verificar-integraciones.yml` | Ejecución manual | Comprueba la conexión con los servicios externos sin escribir datos. |

## Condiciones para publicar o desplegar

- Los trabajos de despliegue se ejecutan solamente en `push` a `main`, después de las pruebas.
- Azure, Google Cloud y AWS se autentican mediante OIDC; no se guardan llaves permanentes de
  proveedor en el repositorio.
- Los recursos y los valores del entorno `produccion` los crean los scripts de
  [infra/](../../infra/README.md). Los secretos de la aplicación (bases, correo, avisos, firmas)
  se cargan una vez en ese mismo entorno.
- [scripts/variables_ejecucion.py](../scripts/variables_ejecucion.py) entrega a cada nube la
  configuración de su servicio: secretos de la Container App en Azure, variables de la revisión en
  Cloud Run y variables de la función en Lambda. Si falta un valor, el despliegue se detiene.
- Azure Container Apps descarga las imágenes privadas de GHCR con la credencial `GHCR_READ_TOKEN`.
- La auditoría Java usa el secreto `NVD_API_KEY` (llave gratuita de la NVD) y guarda su base en
  caché entre ejecuciones.

## Ejecutar y revisar

Desde la raíz, consulta ejecuciones con:

```powershell
gh run list
gh run view ID_DE_EJECUCION --log-failed
```

Las pruebas unitarias de Identidad utilizan SQLite y las de Pagos usan H2; el E2E también corre contra SQL Server. No se debe
interpretar su éxito como validación de procedimientos, tipos nativos o paquetes en SQL Server,
Oracle o MongoDB.
