# Portal ExpoNexo

**React 19 · TypeScript · Vite · PWA**

Aplicación web en español para expositores, visitantes, personal y administradores. Incluye
registro, inicio de sesión en dos pasos, eventos, stands, reservas, entradas, agenda y mesa de
ayuda. La pantalla de ingreso tiene una animación de entrada respetuosa con
`prefers-reduced-motion`.

## Contratos de API

La sesión del portal mantiene tokens en memoria. Algunas rutas y campos de las APIs todavía están
en español; el portal conserva esos contratos legados hasta que proveedor y consumidores puedan
migrar coordinadamente. ADR-012 y ADR-014 describen el destino técnico en inglés y JSON
`snake_case`; consulta [CONTRATOS-API.md](../docs/CONTRATOS-API.md).

Las variables `VITE_` se incluyen en el JavaScript público y solo deben contener direcciones o
configuración no sensible.

## Pantalla de mantenimiento

Si un servicio responde 502, 503 o 504, o no responde, `src/api/mantenimiento.ts` lo informa y el
portal muestra la pantalla **Estamos preparando el recinto** en lugar de un error. Cada 30 segundos
consulta `/salud` del servicio caído y vuelve sola a la pantalla normal cuando responde; no
reintenta acciones del usuario, para no duplicarlas.

## Capturas del manual

Cada cambio en esta carpeta dispara el workflow `capturas-manual.yml`, que regenera las imágenes de
[docs/img/manual/](../docs/img/manual/) contra producción y las sube si cambiaron.

## Desarrollo y comprobaciones

Desde esta carpeta:

```powershell
npm ci
npm run dev
npm test
npm run build
npm run preview
```

Vite muestra el portal en `http://localhost:5173`. La compilación ejecuta TypeScript y genera la
PWA. Para auditar las dependencias de producción:

```powershell
npm audit --omit=dev
```
