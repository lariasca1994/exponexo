# Diseño visual

Tú eliges la plantilla o el sistema de diseño; aquí está **qué buscar** y **cómo adaptarlo** para
que el portal se vea profesional y coherente.

## 1. Qué buscar

| Opción | Qué es | Busca |
|---|---|---|
| Plantilla de panel administrativo | Diseño completo con menú lateral, tablas y formularios | «free React admin dashboard template TypeScript», «Tailwind admin template free» |
| Biblioteca de componentes | Botones, formularios, tablas y modales ya hechos | «shadcn/ui», «Mantine», «Chakra UI», «MUI» |
| Solo CSS | Estilos sin componentes | «Tailwind CSS», «Open Props», «Pico CSS» |

**Cómo elegir:** revisa la licencia (debe permitir uso libre en un proyecto público), que sea
accesible (contraste, navegación con teclado) y que tenga tema claro y oscuro. Anota la elección
en [DECISIONES.md](DECISIONES.md).

## 2. Identidad visual de ExpoNexo

Define antes de adaptar:

| Elemento | Qué decidir |
|---|---|
| Color principal | El color de marca (botones principales, enlaces). |
| Color de acento | Para estados destacados (stand reservado, alerta). |
| Colores de estado | Disponible, reservado, pagado, vencido; éxito, aviso y error. |
| Tipografía | Una para títulos y otra (o la misma) para textos. Busca en «Google Fonts». |
| Ícono y logo | Algo que diga «ferias» o «conexión». Busca «free SVG icons» (por ejemplo, Lucide o Heroicons). |

Estudia: «design tokens», «CSS custom properties», «WCAG color contrast checker».

## 3. Cómo adaptarlo

1. Guarda todos los colores, tamaños y espacios como **variables** (tokens) en un solo lugar, con
   sus valores para tema claro y oscuro.
2. Los componentes usan solo esas variables: nunca un color escrito directo.
3. Define las pantallas base: portada pública, ingreso (con su panel de marca, como en tus otros
   proyectos), panel con menú lateral por rol, tabla con filtros, formulario y modal.
4. Diseña primero para celular y luego para escritorio (busca «mobile first CSS»).
5. Revisa la accesibilidad con la extensión «axe DevTools» o con Lighthouse en Chrome.

## 4. Pantallas que necesitarás

Portada · Registro · Ingreso · Segundo paso · Configurar app autenticadora · Seguridad del perfil ·
Eventos · Plano de stands · Mis reservas · Pagar (QR) · Mis facturas · Mi entrada · Agenda de
citas · Tickets (bandeja y detalle) · Dispositivos · Tablero del administrador · Administración
del catálogo · Pantalla de espera mientras despiertan los servicios · Página sin conexión (PWA).
