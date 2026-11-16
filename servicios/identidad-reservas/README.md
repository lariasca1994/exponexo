# Identidad, reservas y agenda

**Python · FastAPI · SQLAlchemy · Alembic**

Gestiona el registro, el ingreso con verificación en dos pasos y llaves de acceso, y el catálogo,
las reservas de stands, las entradas y la agenda.

## Configuración

Usa `.env.example` como referencia y crea un `.env` local con tus propios valores (no se sube al
repositorio). En desarrollo y pruebas el servicio funciona con SQLite.

## Comandos

Desde esta carpeta, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest pruebas -v
uvicorn app.main:create_app --factory --reload
```

La documentación de la API local está en `/docs`. Para generar la imagen:
`docker build -t exponexo-identidad .`

Se publica solo desde GitHub en cada cambio a `main`, si pasan las pruebas. Los registros operativos
con más de 15 días se depuran automáticamente.
