# Identidad, reservas y agenda

**Python · FastAPI · SQL Server (Azure SQL) · Azure Container Apps**

Es el servicio central: cuentas, verificación en dos pasos, llaves de acceso y emisión de tokens
para todo ExpoNexo; además, el catálogo de eventos, pabellones y stands, las reservas, las entradas
y la agenda de citas.

## Qué debes construir aquí

| Fase | Funcionalidad |
|---|---|
| 1 | Registro, ingreso en dos pasos (app o correo), códigos de respaldo, tokens RS256 y JWKS, llaves de acceso |
| 2 | Catálogo (eventos, pabellones, stands) y reservas con el procedimiento `reservar_stand` |
| 4 | Bandeja de salida y rutas internas que llama el repartidor |
| 5 | Entradas con QR y agenda de citas |
| 7 | Resumen para el tablero |

## Archivos que vas a crear (estructura sugerida)

```text
identidad-reservas/
├── app/
│   ├── main.py            Crea la aplicación, registra las rutas, CORS, manejo de errores y el
│   │                      middleware que agrega el X-Correlation-Id.
│   ├── config.py          Lee el .env con pydantic-settings; el resto del código solo usa esto.
│   ├── db.py              Motor y sesión de SQLAlchemy hacia SQL Server.
│   ├── seguridad/
│   │   ├── contrasenas.py Hash y verificación con Argon2.
│   │   ├── tokens.py      Firma de JWT RS256, verificación y publicación del JWKS.
│   │   ├── mfa.py         TOTP (clave, QR, verificación sin reutilizar códigos) y códigos por correo.
│   │   ├── llaves.py      Registro e ingreso con WebAuthn.
│   │   ├── cifrado.py     Cifrado de la clave TOTP antes de guardarla.
│   │   └── dependencias.py «Usuario actual» y «exige rol X» para usar en las rutas.
│   ├── modelos/           Clases de SQLAlchemy (una por tabla del modelo de datos).
│   ├── esquemas/          Modelos de Pydantic de entrada y salida de cada ruta.
│   ├── rutas/             Un archivo por grupo: cuentas, sesion, perfil, catalogo, reservas,
│   │                      entradas, agenda, admin, interno y salud.
│   ├── servicios/         Lógica de negocio: lo que las rutas llaman (incluye la llamada a los
│   │                      procedimientos almacenados y el envío de correos con Brevo).
│   └── tareas/            Procesos periódicos: vencer reservas y publicar la bandeja de salida.
├── migraciones/           Alembic: tablas y procedimientos almacenados versionados.
├── pruebas/               pytest: unitarias y de integración.
├── requirements.txt       Dependencias (lo generas tú).
├── alembic.ini            Lo crea `alembic init`.
├── Dockerfile             Imagen para producción (fase 9).
├── .env.example           Plantilla de variables (ya está).
└── .env                   Tu copia con valores reales (no se sube).
```

## Qué estudiar antes

Bloques 1, 2 y 5 de la [ruta de aprendizaje](../../docs/RUTA-DE-APRENDIZAJE.md). Tablas en la
sección 1 del [modelo de datos](../../docs/MODELO-DE-DATOS.md) y rutas en la sección 1 de los
[contratos de API](../../docs/CONTRATOS-API.md).

## Comandos de este servicio

| Para qué | Comando (desde esta carpeta) |
|---|---|
| Copiar la plantilla de variables | `Copy-Item .env.example .env` |
| Crear y activar el entorno virtual | `python -m venv .venv` y `.venv\Scripts\Activate.ps1` |
| Instalar dependencias | Ver la fase 1 del [manual](../../docs/MANUAL-DESARROLLO.md); luego `pip install -r requirements.txt` |
| Migraciones | `alembic revision --autogenerate -m "mensaje"` y `alembic upgrade head` |
| Levantar | `uvicorn app.main:app --reload --port 8001` |
| Documentación de la API | `http://127.0.0.1:8001/docs` |
| Pruebas | `pytest -q` |
| Construir la imagen | `docker build -t exponexo-identidad .` |
| Probar la imagen | `docker run --env-file .env -p 8001:8001 exponexo-identidad` |

## Generar las claves de los tokens

Necesitas un par de claves RSA (privada para firmar, pública para el JWKS). Investiga: «generate
RSA key pair 2048 openssl» o «cryptography generate RSA private key Python». Guarda la privada
**fuera del repositorio** (la carpeta `claves/` está en el `.gitignore` por la extensión `.pem`).

## Lista de chequeo del servicio

- [ ] `GET /salud` responde sin autenticación.
- [ ] El JWKS publica la clave pública con su `kid`.
- [ ] Ninguna contraseña ni código se guarda en claro.
- [ ] Las reservas usan el procedimiento almacenado y soportan dos intentos simultáneos.
- [ ] Toda ruta de administración exige el rol administrador.
- [ ] Las rutas internas rechazan tokens de personas.
