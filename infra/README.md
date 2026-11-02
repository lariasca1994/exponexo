# Recursos en la nube

Guía de lo que debes crear en cada nube, **solo en planes gratuitos**. Créalo cuando la fase lo
necesite, no todo de una vez. Anota en tu `.env` (nunca aquí) los datos que te entregue cada nube.

> Regla: si una pantalla te pide elegir un plan, elige siempre el gratuito y verifica que no haya
> cobros automáticos al terminar una prueba. Activa las alertas de presupuesto en cada nube.

## Fase 1 · SQL Server (Azure SQL)

1. En el portal de Azure, crea un **grupo de recursos** para ExpoNexo.
2. Crea un **Azure SQL Database** usando la **oferta gratuita** (busca «Azure SQL Database free
   offer»). Al crearla, configura que al agotar la cuota se **pause** (nunca que cobre).
3. Crea el servidor con autenticación de SQL (usuario y contraseña) o, mejor, investiga la
   autenticación con Microsoft Entra.
4. En «Redes», permite tu IP para conectarte desde tu equipo.
5. Copia servidor, base, usuario y contraseña al `.env` de identidad-reservas.

Busca: «Azure SQL Database free offer create», «Azure SQL firewall rule client IP», «Azure SQL
auto-pause serverless».

## Fase 3 · Oracle Autonomous Database

1. En Oracle Cloud, crea una **Autonomous Database Always Free** (tipo transaccional).
2. Crea un usuario propio para la aplicación (no uses ADMIN en la app). Investiga los permisos
   mínimos que necesita.
3. Descarga el **wallet** («Database connection» → «Download wallet») y guárdalo fuera del
   repositorio.
4. Copia el alias de conexión, usuario, contraseña y ruta del wallet al `.env` de pagos.

Busca: «Oracle Always Free Autonomous Database», «Oracle create user grant privileges», «Oracle
Autonomous Database download wallet».

## Fase 4 · AWS (colas y funciones)

1. Crea las colas `exponexo-eventos` y `exponexo-eventos-errores` (comandos en la fase 4 del
   [manual](../docs/MANUAL-DESARROLLO.md)).
2. Crea las funciones `exponexo-repartidor` y `exponexo-avisos` con el runtime de Python, y
   conecta cada una a su cola (investiga «Lambda event source mapping SQS»).
3. Crea un usuario de IAM **solo para tu equipo local** con permisos mínimos sobre las colas
   (investiga «IAM least privilege SQS policy»).
4. Activa la retención de logs de 14 días en las funciones.

Busca: «AWS free tier always free SQS Lambda», «IAM policy sqs:SendMessage resource».

## Fase 6 · MongoDB Atlas

1. Crea un clúster **M0 gratuito**.
2. Crea un usuario de base de datos con permisos solo sobre la base `exponexo_mesa`.
3. En «Network Access», permite tu IP (y luego la salida de Azure; investiga cómo, o el acceso
   desde cualquier IP con usuario y contraseña fuertes).
4. Copia la cadena de conexión al `.env` de mesa-ayuda.

Busca: «MongoDB Atlas M0 free cluster», «Atlas database user specific database role».

## Correo y avisos (fases 1 y 4)

| Servicio | Qué crear | Dónde se obtiene |
|---|---|---|
| Brevo | Cuenta gratuita, remitente verificado y una API key | Brevo → SMTP & API → API Keys |
| Telegram | Un bot y un grupo para el personal | @BotFather en Telegram; investiga «get Telegram chat id» |

## Fase 9 · Despliegue

| Parte | Dónde | Qué crear |
|---|---|---|
| Portal | Vercel | Proyecto conectado al repositorio, con la carpeta raíz `portal/` y sus variables `VITE_`. |
| Identidad-reservas y mesa-ayuda | Azure Container Apps | Un entorno y dos Container Apps con escala mínima 0. |
| Pagos | Google Cloud Run | Un proyecto, el servicio con instancias mínimas 0 y un repositorio de Artifact Registry con política de limpieza. |
| Despliegue sin claves | GitHub ↔ cada nube | Federación OIDC: Azure (identidad administrada o app registrada con credencial federada), Google (Workload Identity Federation) y AWS (rol con proveedor OIDC de GitHub). |

Busca: «Azure Container Apps min replicas 0», «Cloud Run min instances 0 free tier», «Artifact
Registry cleanup policy», «GitHub OIDC Azure federated credential», «Workload Identity Federation
GitHub Actions», «AWS IAM OIDC provider GitHub Actions».

## Secretos que tendrás en GitHub (fase 9)

Los mismos nombres que en los `.env.example` de cada servicio, cargados con
`gh secret set NOMBRE --body "valor"`. Nunca subas un `.env` ni escribas valores reales en este
archivo.
