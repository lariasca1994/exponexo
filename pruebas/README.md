# Pruebas transversales

Aquí viven las pruebas que cruzan servicios: los recorridos E2E del portal y las pruebas de
contrato de cada API. Las pruebas unitarias y de integración de cada servicio viven dentro de su
propia carpeta.

## Qué vas a crear

| Carpeta | Herramienta | Qué prueba |
|---|---|---|
| `e2e/` | Playwright | Recorridos completos en el navegador: registro con segundo paso, reservar y pagar un stand, comprar una entrada, pedir y aceptar una cita, abrir un ticket. |
| `contratos/` | Schemathesis (u otra que elijas) | Que cada API responda lo que dice su OpenAPI, también ante datos inesperados. |

Cuando el flujo principal funcione en producción, súmalo a **qa-evidencia** (con su cuenta de
prueba y su secreto TOTP, como los demás proyectos) y a **portafolio-status** (monitoreo de salud).

## Qué estudiar

Bloque 8 de la [ruta de aprendizaje](../docs/RUTA-DE-APRENDIZAJE.md). Para Playwright: selectores
por rol y texto (`getByRole`, `getByLabel`), esperas automáticas, trazas y el patrón «Page Object
Model». Para el segundo paso en E2E: cómo calcular un código TOTP desde el secreto de una cuenta de
prueba.

## Comandos

| Para qué | Comando (desde `pruebas/`) |
|---|---|
| Crear el proyecto de Playwright | `npm init playwright@latest` |
| Correr las pruebas | `npx playwright test` |
| Ver el reporte | `npx playwright show-report` |
| Modo con interfaz para depurar | `npx playwright test --ui` |
| Generador de selectores | `npx playwright codegen http://localhost:5173` |
| Instalar Schemathesis | `pip install schemathesis` |
| Probar un contrato | `st run http://localhost:8001/openapi.json` |

## Reglas

- Cuentas y datos de prueba **inventados**; los secretos solo en `.env` y en los secretos de GitHub.
- Cada prueba deja los datos como los encontró o usa datos únicos (por ejemplo, con la fecha y
  hora en el nombre).
- Las pruebas E2E apuntan a producción solo desde qa-evidencia; en local, a tus servicios locales.
