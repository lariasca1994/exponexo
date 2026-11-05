# Identidad, reservas y agenda

**Python · FastAPI · SQLAlchemy · Alembic · SQL Server**

Emite sesiones JWT RS256 y JWKS, gestiona registro, MFA y passkeys, y proporciona catálogo,
reservas de stands, entradas y agenda. La API y el esquema existentes aún conservan nombres en
español; consulta [DECISIONES.md](../../docs/DECISIONES.md) antes de cambiar contratos o datos.

## Configuración

Usa `.env.example` como referencia y crea un `.env` local. El servicio admite SQLite en desarrollo
y pruebas; en producción debe recibir la configuración SQL Server, claves RSA y clave simétrica
reales. La validación de configuración rechaza los valores de desarrollo en producción. `APP_ENTORNO`
es el nombre canónico; `ENTORNO` se acepta como compatibilidad con los workflows existentes.

No se declara compatibilidad de producción con SQLite. La CI corre las pruebas con SQLite y no
ejecuta los procedimientos almacenados sobre una instancia SQL Server.

## Comandos

Ejecuta desde esta carpeta en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest pruebas -v
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001 --reload
```

La documentación OpenAPI local está en `http://127.0.0.1:8001/docs`. Para generar la imagen:

```powershell
docker build -t exponexo-identidad .
```

## CI/CD

`.github/workflows/identidad-reservas.yml` prueba con Python 3.14 y SQLite. En `main`, publica en
GHCR y actualiza Azure Container Apps mediante OIDC, con su configuración como secretos de la
Container App. Antes de publicar la revisión, el workflow aplica las migraciones pendientes en
Azure SQL (`alembic upgrade head`, con reintentos mientras la base despierta). Al arrancar, el
contenedor escribe la llave JWT desde `JWT_CLAVE_PRIVADA_PEM` y levanta la API; si la configuración
es inválida, no arranca.
La bandeja de salida se publica en el tema SNS (`SNS_TEMA_EVENTOS_ARN`) justo después de cada
operación que escribe, sin sondeos periódicos: así Azure SQL se pausa cuando nadie usa el servicio y
no se consume su cuota gratuita. Las cuentas fijas de administración, personal y QA llegan en el
secreto `USUARIOS_INICIALES` y el workflow las crea o ajusta después de las migraciones. El registro público solo permite elegir visitante (por
defecto) o expositor.

## Depuración cada 15 días

`app/services/depuracion.py` borra los registros operativos con más de 15 días: intentos de
ingreso, auditoría, códigos de verificación usados o vencidos, sesiones vencidas o revocadas,
eventos ya publicados de la bandeja de salida y eventos procesados. Lo ejecuta el workflow
`depuracion.yml` los días 1 y 16 de cada mes (`python -m app.services.depuracion`), para que la
base no crezca hasta salirse de la cuota gratuita.
