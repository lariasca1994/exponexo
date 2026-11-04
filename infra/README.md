# Despliegue e infraestructura

Los recursos de cada nube se crean **una sola vez** con los scripts de esta carpeta; desde ahí, todo
despliegue sale de GitHub Actions con cada push a `main`. Los scripts son idempotentes: si un recurso
ya existe lo dejan como está y solo completan lo que falte. Al terminar, cada uno guarda en el
entorno `produccion` de GitHub los valores que necesitan los workflows.

| Script | Crea | Uso |
|---|---|---|
| [aws/crear.sh](aws/crear.sh) | Tema SNS, una cola SQS con DLQ por función, las 2 Lambdas con su activador, rol de despliegue OIDC y un usuario que solo publica en el tema | `bash infra/aws/crear.sh` |
| [azure/crear.sh](azure/crear.sh) | Entorno de Container Apps sin Log Analytics, las apps de identidad y mesa de ayuda, acceso a GHCR e identidad OIDC con permiso solo sobre el grupo | `bash infra/azure/crear.sh <grupo>` |
| [gcp/crear.sh](gcp/crear.sh) | Proyecto, Artifact Registry con limpieza automática, cuentas de servicio y federación con GitHub | `bash infra/gcp/crear.sh <proyecto> <región>` |

## Destinos

| Servicio | Destino | Registro | Configuración en ejecución |
|---|---|---|---|
| Identidad y Reservas | Azure Container Apps | GHCR | Secretos de la Container App |
| Mesa de ayuda | Azure Container Apps | GHCR | Secretos de la Container App |
| Pagos | Google Cloud Run | Artifact Registry | Variables de la revisión (el wallet de Oracle llega como zip en base64) |
| Eventos | AWS Lambda | Paquetes ZIP | Variables de la función |
| Portal | Vercel (integración con GitHub, carpeta `portal`) | — | Variables `VITE_*` del proyecto |

Los workflows arman esa configuración con
[.github/scripts/variables_ejecucion.py](../.github/scripts/variables_ejecucion.py) a partir de los
secretos y variables del entorno `produccion`; si falta alguno, el despliegue se detiene antes de
tocar la nube. Los servicios, a su vez, se niegan a arrancar en producción con configuración
incompleta.

## Eventos

Cada servicio guarda sus eventos en su bandeja de salida y los publica en el tema SNS. El tema
reparte cada evento a una cola por función (entrega directa del mensaje, sin envoltura de SNS);
tras 5 intentos fallidos el mensaje pasa a la cola de errores de esa función.

## Datos y costo cero

Cada recurso se crea solo en su plan gratuito; si no tiene opción gratuita, no se usa. Las imágenes
viejas se depuran (GHCR conserva 5 por servicio y Artifact Registry 2), los logs de Lambda vencen a
los 14 días y el entorno de Container Apps no envía logs a Log Analytics. No guardes wallets,
archivos `.env`, claves ni credenciales en esta carpeta.

Para el orden completo del primer despliegue, consulta el
[manual de desarrollo](../docs/MANUAL-DESARROLLO.md) y [los workflows](../.github/workflows/README.md).
