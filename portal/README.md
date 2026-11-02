# Portal

**React · TypeScript · Vite · PWA · Vercel**

Una sola interfaz para todos los roles: expositores, visitantes, personal del recinto y
administradores. Habla con los tres servicios por HTTPS con el token que entrega identidad.

## Qué debes construir aquí

| Fase | Pantallas |
|---|---|
| 1 | Portada, registro, ingreso, segundo paso, configurar app autenticadora, seguridad del perfil, llaves de acceso, PWA |
| 2 | Eventos, plano de stands, mis reservas, administración del catálogo |
| 3 | Pagar con QR, mis facturas |
| 5 | Mi entrada (QR), agenda de citas |
| 6 | Tickets (crear, bandeja, detalle), dispositivos |
| 7 | Tablero del administrador |

## Archivos que vas a crear (estructura sugerida)

Vite crea la base (`index.html`, `vite.config.ts`, `tsconfig`, `src/main.tsx`, `src/App.tsx`).
Tú organizas `src/` así:

```text
portal/src/
├── main.tsx           Punto de entrada (lo crea Vite): monta la app, el router y TanStack Query.
├── App.tsx            Rutas de la aplicación y diseño general (menú según el rol).
├── api/               Un cliente por servicio (identidad, pagos, mesa) que agrega el token y el
│                      X-Correlation-Id, y traduce los errores Problem Details a mensajes.
├── sesion/            Estado de la sesión: token en memoria, refresco, cierre de sesión y
│                      «ruta protegida por rol».
├── paginas/           Una carpeta por área: acceso, eventos, reservas, pagos, entradas, agenda,
│                      tickets, dispositivos, tablero, admin.
├── componentes/       Piezas reutilizables: botones, formularios, tabla, modal, aviso, plano de
│                      stands, QR.
├── estilos/           Variables de diseño (tokens) y estilos globales (ver docs/DISENO.md).
└── tipos/             Tipos de TypeScript de lo que devuelve cada API.
```

En `public/` irán el ícono, el manifiesto de la PWA y la página sin conexión.

## Qué estudiar antes

Filas de React, TypeScript, React Router, TanStack Query y PWA del bloque 1 de la
[ruta de aprendizaje](../docs/RUTA-DE-APRENDIZAJE.md); [diseño visual](../docs/DISENO.md).

**Las variables `VITE_` son públicas:** terminan dentro del JavaScript que descarga cualquier
visitante. Nunca pongas secretos ahí; solo direcciones de los servicios.

## Comandos

| Para qué | Comando |
|---|---|
| Crear el proyecto (desde `exponexo/`, solo la primera vez) | `npm create vite@latest portal -- --template react-ts`. Vite avisará que la carpeta no está vacía: elige **«Ignore files and continue»**. **No** elijas «Remove existing files», porque borraría este README y el `.env.example`. |
| Instalar dependencias | `npm install` |
| Paquetes de la fase 1 | `npm install react-router-dom @tanstack/react-query` y `npm install -D vite-plugin-pwa` |
| Copiar la plantilla de variables | `Copy-Item .env.example .env` |
| Levantar en desarrollo | `npm run dev` (abre `http://localhost:5173`) |
| Revisar tipos | `npx tsc --noEmit` |
| Compilar para producción | `npm run build` y `npm run preview` para probar la compilación |
| Auditar dependencias | `npm audit --omit=dev` |

## Lista de chequeo

- [ ] Ninguna pantalla protegida se ve sin sesión.
- [ ] El menú muestra solo lo que el rol puede usar (y el servicio igual lo valida).
- [ ] Los errores de la API se muestran como mensajes claros, no como JSON.
- [ ] Mientras un servicio despierta, se ve la pantalla de espera.
- [ ] La PWA se instala y muestra la página sin conexión.
- [ ] Funciona en celular.
