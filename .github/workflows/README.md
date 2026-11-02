# Workflows de GitHub Actions

En la fase 9 crearás aquí un workflow por servicio. Este archivo describe **qué debe hacer** cada
uno; la configuración la escribes tú siguiendo la documentación de GitHub Actions.

## Workflows a crear

| Archivo | Se dispara con | Pasos |
|---|---|---|
| `identidad-reservas.yml` | push a `main` que cambie `servicios/identidad-reservas/**` | Pruebas (pytest) → construir imagen → publicar → actualizar la Container App → comprobar `GET /salud`. |
| `pagos.yml` | push a `main` que cambie `servicios/pagos/**` | Pruebas (`mvnw test`) → construir imagen → publicar en Artifact Registry → desplegar en Cloud Run → comprobar `/actuator/health`. |
| `mesa-ayuda.yml` | push a `main` que cambie `servicios/mesa-ayuda/**` | Pruebas (`dotnet test`) → construir imagen → publicar → actualizar la Container App → comprobar la salud. |
| `eventos.yml` | push a `main` que cambie `servicios/eventos/**` | Pruebas (pytest) → empaquetar → actualizar el código de las dos funciones → fijar retención de logs. |
| `portal` | (sin workflow) | Lo publica Vercel con su integración de Git en cada push. |
| `depuracion.yml` | días 1 y 16 de cada mes y a mano | Borrar imágenes viejas (conservar unas pocas) y cachés sin uso. |
| `seguridad.yml` | semanal y en cada pull request | Auditoría de dependencias de los cuatro servicios y del portal. |

## Qué estudiar

Bloque 9 de la [ruta de aprendizaje](../../docs/RUTA-DE-APRENDIZAJE.md). Busca: «GitHub Actions
on push paths», «GitHub Actions jobs needs», «GitHub Actions environments secrets», «GitHub
Actions OIDC permissions id-token write», «actions/setup-python», «actions/setup-java
distribution temurin», «actions/setup-dotnet», «docker/build-push-action», «azure/login»,
«google-github-actions/auth», «aws-actions/configure-aws-credentials», «GitHub Actions schedule
cron», «actions/delete-package-versions».

## Reglas

- Despliegue sin claves guardadas: OIDC hacia cada nube.
- Un workflow por servicio, que solo corre si cambió su carpeta.
- Los mensajes de commit de solo documentación llevan `[skip ci]`.
- Comprueba con `gh run list` y `gh run view --log-failed` cuando algo falle.
