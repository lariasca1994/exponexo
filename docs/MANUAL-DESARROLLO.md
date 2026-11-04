# Manual de desarrollo de ExpoNexo

Guía operativa para trabajar con el código que ya existe en este monorepositorio. Los README de
cada servicio describen sus responsabilidades y comandos; este manual reúne el entorno local, las
pruebas, la configuración y los flujos de CI/CD. No presupone que una nube, una base de producción
o un secreto de GitHub ya estén configurados.

## Contenido

1. [Estado y convenciones](#1-estado-y-convenciones)
2. [Herramientas](#2-herramientas)
3. [Ejecución local](#3-ejecución-local)
4. [Pruebas](#4-pruebas)
5. [Configuración y secretos](#5-configuración-y-secretos)
6. [CI/CD y despliegues](#6-cicd-y-despliegues)
7. [Revisión antes de integrar](#7-revisión-antes-de-integrar)

## 1. Estado y convenciones

El repositorio contiene un portal React, cuatro servicios y pruebas. Que el código o un workflow
exista no demuestra por sí solo que un despliegue haya ocurrido o que una base administrada esté
configurada.

Convenciones vigentes en todo el código:

- ADR-012: clases, funciones y variables en inglés; tablas, columnas, procedimientos, rutas,
  propiedades JSON, tipos de evento y variables de entorno en español.
- ADR-013: UUID generado por la aplicación y guardado como texto en las tres bases.
- ADR-014: JSON en `snake_case` en todas las APIs.

Antes de cambiar un contrato o esquema, coordina proveedor, portal, consumidores de eventos,
migraciones y procedimientos almacenados. Una vez en producción, no reescribas migraciones ya
aplicadas: crea una nueva.
Consulta [DECISIONES.md](DECISIONES.md), [MODELO-DE-DATOS.md](MODELO-DE-DATOS.md) y
[CONTRATOS-API.md](CONTRATOS-API.md) para el estado y la estrategia de compatibilidad.

La documentación narrativa, los mensajes para las personas y la interfaz permanecen en español.
Los nombres técnicos se escriben en inglés conforme se migren los contratos.

## 2. Herramientas

Instala Git, Docker Desktop, Node.js, Python, Java, .NET y los clientes de nube que necesites.
Las versiones exactas usadas por CI están declaradas en cada workflow; consulta esos archivos
antes de reproducir una ejecución local. Actualmente CI usa Python 3.14, Java 25 y .NET 10.

Para desarrollo nativo también se requieren:

- ODBC Driver 18 para SQL Server al usar SQL Server desde Identidad y Reservas.
- Para Pagos basta Java 25: el Maven Wrapper (`mvnw`) descarga la versión de Maven del proyecto.
- Las CLI de Azure, Google Cloud y AWS solo para operaciones de sus respectivas nubes.

## 3. Ejecución local

### Docker Compose

Desde la raíz:

```powershell
docker compose up --build
```

El entorno local usa SQLite para Identidad, el perfil de desarrollo para Pagos y configuración de
desarrollo para Mesa de ayuda. No lo uses como configuración de producción ni como prueba de
compatibilidad con SQL Server, Oracle o MongoDB.

| Componente | Dirección local |
|---|---|
| Portal | `http://localhost:8080` |
| Identidad y Reservas | `http://localhost:8001/docs` |
| Pagos | `http://localhost:8002/actuator/health` |
| Mesa de ayuda | `http://localhost:8003/salud` |

Para detener los contenedores, ejecuta `docker compose down` desde la raíz.

### Servicios individuales

**Portal**, desde `portal/`:

```powershell
npm ci
npm run dev
```

**Identidad y Reservas**, desde `servicios/identidad-reservas/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8001 --reload
```

**Pagos**, desde `servicios/pagos/`:

```powershell
mvn test
mvn spring-boot:run
```

**Mesa de ayuda**, desde `servicios/mesa-ayuda/`:

```powershell
dotnet run --project src/MesaAyuda.Api
```

**Eventos**, desde `servicios/eventos/`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest pruebas -v
```

## 4. Pruebas

Ejecuta cada comando desde la carpeta que se indica. En PowerShell, usa rutas con `\`.

| Componente | Comando |
|---|---|
| Portal | `npm test` y `npm run build` (desde `portal/`) |
| Identidad y Reservas | `python -m pytest pruebas -v` (desde `servicios/identidad-reservas/`) |
| Pagos | `mvn test -B` (desde `servicios/pagos/`) |
| Mesa de ayuda | `dotnet test MesaAyuda.sln` (desde `servicios/mesa-ayuda/`) |
| Eventos | `python -m pytest pruebas -v` (desde `servicios/eventos/`) |
| Integración E2E | `python -m pytest pruebas/test_e2e_integration.py -v` (desde la raíz) |

Las suites de CI no validan actualmente los procedimientos en instancias SQL Server/Oracle reales.
Las pruebas con SQLite y H2 no sustituyen esa verificación ni una prueba contra MongoDB real.
Revisa los resultados de Actions y los registros de cada servicio antes de considerar un cambio
validado.

## 5. Configuración y secretos

- Usa `.env.example` como referencia para las variables que cada servicio consume. Los nombres
  implementados son literales: no los renombres sin actualizar código, workflows, despliegue y
  consumidores.
- Para desarrollo, crea el `.env` local con `Copy-Item .env.example .env` en la carpeta del
  servicio. No guardes valores reales en el repositorio ni en esta guía.
- El `.gitignore` excluye `.env`, claves y salidas de compilación. Verifica `git status --short`
  antes de compartir cambios.
- En producción, guarda secretos en el gestor de la plataforma y revisa que cada workflow los
  pase al servicio que los requiere. Los valores ficticios y los defaults de desarrollo no son
  secretos válidos.
- Identidad, Pagos y Mesa de ayuda validan requisitos de configuración cuando se ejecutan en modo
  producción. El perfil de desarrollo puede usar bases o valores locales; no publiques ese perfil
  en un servicio productivo.

## 6. CI/CD y despliegues

Los workflows están en [.github/workflows/](../.github/workflows/README.md). En general, las
solicitudes de cambio ejecutan pruebas; los `push` a `main` pueden publicar y desplegar, si existen
los secretos, permisos OIDC, recursos y nombres de servicios necesarios.

| Flujo | Publicación y destino |
|---|---|
| Identidad y Reservas | GHCR y actualización de Azure Container Apps |
| Pagos | Google Artifact Registry y Cloud Run |
| Mesa de ayuda | GHCR y actualización de Azure Container Apps |
| Eventos | Paquetes de Lambda y despliegue en AWS |

Identidad y Mesa de ayuda requieren que Azure Container Apps pueda descargar la imagen de GHCR
 pública o mediante credenciales de registry. Si la imagen es privada, configura `GHCR_READ_TOKEN`
con permiso de lectura de paquetes en el entorno de GitHub `produccion`; el workflow lo aplica a la
Container App. Todo debe quedar en planes gratuitos: antes de crear un recurso, confirma que
tiene opción gratuita, y configura la limpieza de imágenes y logs viejos para no salir de ella.

Los workflows autentican a las nubes mediante OIDC. No agregues claves permanentes al código ni
crees un despliegue manual como sustituto de un workflow fallido. Confirma la ejecución en GitHub
Actions y comprueba la salud del servicio después de desplegar.

## 7. Revisión antes de integrar

1. Ejecuta las pruebas del componente afectado y revisa el resultado, no solo el código de salida.
2. Ejecuta `git diff --check` y revisa el diff completo.
3. Actualiza el README y los documentos técnicos directamente relacionados con el cambio.
4. Comprueba que no se hayan incluido `.env`, credenciales, claves privadas, datos personales ni
   artefactos de compilación.
5. Para cambios de API, eventos, IDs o tablas, valida compatibilidad y migraciones con cada
   consumidor antes de desplegar.
